import os
import requests
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACES_DETAIL_FIELDS = "name,formatted_address,formatted_phone_number,website,opening_hours,rating,user_ratings_total,business_status,types"
PROSPEO_DOMAIN_URL = "https://api.prospeo.io/domain-search"
OPENWEBNINJA_URL = "https://api.openwebninja.com/real-time-web-search/search"
BLITZ_BASE_URL = os.environ.get("BLITZ_BASE_URL", "https://api.useblitz.com")
MV_VERIFY_URL = "https://api.millionverifier.com/api/v3/"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-4o-mini"
LOCAL_BIZ_SEARCH_URL = "https://api.openwebninja.com/local-business-data/search"
WEBSITE_CONTACTS_URL = "https://api.openwebninja.com/website-contacts-scraper/get-contacts"
YELP_SEARCH_URL = "https://api.openwebninja.com/yelp-business-data/search"

NEWS_BLOCKLIST = ["obituary", "wikipedia", "jobs.", "careers.", "lawsuit", "indictment"]

SENIOR_KEYWORDS = [
    "owner", "founder", "ceo", "president", "coo", "cto", "cfo",
    "director", "manager", "principal", "partner", "vp",
    "vice president", "head of", "chief", "proprietor", "operator", "managing",
    "attorney", "lawyer", "counsel", "associate", "esquire",
    "agent", "broker", "advisor", "consultant", "realtor",
]

NOISE_TYPES = {"point_of_interest", "establishment", "food", "store", "premise", "geocode"}


def extract_domain(url):
    if not url:
        return None
    host = urlparse(url).netloc or url
    return host.removeprefix("www.").split("/")[0].split("?")[0]


def is_senior(position):
    if not position:
        return False
    p = position.lower()
    return any(kw in p for kw in SENIOR_KEYWORDS)


def get_place_candidates(query, api_key):
    r = requests.get(PLACES_SEARCH_URL, params={"query": query, "key": api_key}, timeout=30)
    r.raise_for_status()
    data = r.json()
    status = data.get("status")
    if status == "ZERO_RESULTS":
        return []
    if status != "OK":
        raise ValueError(f"Google Places API error: {status} — {data.get('error_message', '')}")
    return data.get("results", [])


def get_place_details(place_id, api_key):
    r = requests.get(
        PLACES_DETAILS_URL,
        params={"place_id": place_id, "fields": PLACES_DETAIL_FIELDS, "key": api_key},
        timeout=30
    )
    r.raise_for_status()
    return r.json().get("result", {})


def _get_blitz_contacts(domain, blitz_key):
    """Domain → senior contacts (with LinkedIn URLs) + company phone via Blitz."""
    if not domain or not blitz_key:
        return [], None
    try:
        r = requests.post(
            f"{BLITZ_BASE_URL}/api/enrichment/company",
            json={"domain": domain},
            headers={"Authorization": f"Bearer {blitz_key}", "Content-Type": "application/json"},
            timeout=30
        )
        if r.status_code in (404, 402):
            return [], None
        r.raise_for_status()
        data = r.json()
        company = data.get("company", {})
        company_phone = company.get("phone") or None
        employees = data.get("employees", [])
        seniors = [e for e in employees if is_senior(e.get("title", ""))]
        contacts = [{
            "first_name": e.get("first_name", ""),
            "last_name": e.get("last_name", ""),
            "email": e.get("email") or None,
            "position": e.get("title"),
            "linkedin_url": e.get("linkedin_url") or None,
            "source": "blitz",
        } for e in seniors]
        return contacts, company_phone
    except Exception as e:
        logger.warning(f"Blitz enrichment failed for {domain}: {e}")
        return [], None


def _get_prospeo_contacts(domain, api_key):
    """Domain → senior contacts with verified emails via Prospeo."""
    if not domain or not api_key:
        return []
    try:
        r = requests.post(
            PROSPEO_DOMAIN_URL,
            json={"domain": domain, "limit": 10},
            headers={"X-KEY": api_key, "Content-Type": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            return []
        emails = data.get("response", {}).get("emails", [])
        seniors = [e for e in emails if is_senior(e.get("position"))]
        return [{
            "first_name": c.get("first_name", ""),
            "last_name": c.get("last_name", ""),
            "email": c.get("email"),
            "position": c.get("position"),
            "verification_status": c.get("verification_status"),
            "confidence_score": c.get("confidence_score"),
            "source": "prospeo",
        } for c in seniors]
    except Exception as e:
        logger.warning(f"Prospeo domain search failed for {domain}: {e}")
        return []


def get_domain_contacts(domain, blitz_key=None, prospeo_key=None):
    """
    Blitz first for contacts + phone. Prospeo fills email gaps and supplements.
    Returns (contacts_list, company_phone).
    """
    blitz_contacts, company_phone = _get_blitz_contacts(domain, blitz_key)

    # Run Prospeo when: no Blitz key, Blitz found nothing, or some contacts are missing emails
    need_prospeo = prospeo_key and (
        not blitz_contacts or any(not c.get("email") for c in blitz_contacts)
    )
    prospeo_contacts = _get_prospeo_contacts(domain, prospeo_key) if need_prospeo else []

    if not blitz_contacts:
        return prospeo_contacts, company_phone

    # Merge: try to fill missing Blitz emails from Prospeo matches by name
    prospeo_by_name = {}
    for pc in prospeo_contacts:
        key = f"{pc['first_name'].lower().strip()} {pc['last_name'].lower().strip()}"
        prospeo_by_name[key] = pc

    result = []
    seen_emails = set()
    for c in blitz_contacts:
        if not c.get("email"):
            name_key = f"{c['first_name'].lower().strip()} {c['last_name'].lower().strip()}"
            if name_key in prospeo_by_name:
                match = prospeo_by_name[name_key]
                c = {**c, "email": match.get("email"),
                     "verification_status": match.get("verification_status"),
                     "source": "blitz+prospeo"}
        email = c.get("email")
        if email and email in seen_emails:
            continue
        if email:
            seen_emails.add(email)
        result.append(c)

    # Add Prospeo-only contacts not already represented
    for pc in prospeo_contacts:
        if pc.get("email") and pc["email"] not in seen_emails:
            seen_emails.add(pc["email"])
            result.append(pc)

    return result, company_phone


def get_company_news(company_name, owinja_key):
    if not company_name or not owinja_key:
        return None
    try:
        r = requests.get(
            OPENWEBNINJA_URL,
            params={"query": f'"{company_name}" news OR announcement OR blog', "limit": 5},
            headers={"x-api-key": owinja_key},
            timeout=15
        )
        if not r.ok:
            return None
        results = r.json().get("data", [])
        for item in results:
            text = f"{item.get('title','')} {item.get('snippet','')} {item.get('url','')}".lower()
            if any(k in text for k in NEWS_BLOCKLIST):
                continue
            return {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "date": item.get("date", ""),
            }
    except Exception as e:
        logger.warning(f"OpenWebNinja news lookup failed for {company_name}: {e}")
    return None


def get_ai_analysis(name, domain, types, openrouter_key):
    if not name or not openrouter_key:
        return None
    industry = ", ".join(types[:3]) if types else "unknown"
    prompt = (
        f"Given this local business:\n"
        f"Name: {name}\n"
        f"Domain: {domain or 'unknown'}\n"
        f"Type: {industry}\n\n"
        f"Provide:\n"
        f"1. summary: one sentence what they do (max 15 words)\n"
        f"2. category: specific vertical (e.g. 'dental practice', 'Italian restaurant')\n"
        f"3. customer_type: who they serve (max 10 words)\n"
        f"4. cold_email_angle: one specific personalization angle for a cold email (max 20 words)\n\n"
        f'Respond as JSON with exactly these keys: {{"summary","category","customer_type","cold_email_angle"}}'
    )
    try:
        r = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
            json={"model": OPENROUTER_MODEL, "messages": [{"role": "user", "content": prompt}],
                  "response_format": {"type": "json_object"}, "max_tokens": 200},
            timeout=20
        )
        if not r.ok:
            return None
        content = r.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            return None
        import json as _json
        data = _json.loads(content)
        return {
            "summary": data.get("summary", ""),
            "category": data.get("category", ""),
            "customer_type": data.get("customer_type", ""),
            "cold_email_angle": data.get("cold_email_angle", ""),
        }
    except Exception as e:
        logger.warning(f"OpenRouter AI analysis failed for {name}: {e}")
        return None


def verify_email_mv(email, mv_key):
    if not email or not mv_key:
        return None
    try:
        r = requests.get(
            MV_VERIFY_URL,
            params={"api": mv_key, "email": email, "timeout": 10},
            timeout=15
        )
        if not r.ok:
            return None
        data = r.json()
        result = data.get("resultcode") or data.get("result")
        return "valid" if result in (1, "ok") else "invalid"
    except Exception as e:
        logger.warning(f"MillionVerifier check failed for {email}: {e}")
        return None


def _get_local_biz_email(name, address, owinja_key):
    """Search OpenWebNinja Local Business Data API by name to pull business email."""
    if not name or not owinja_key:
        return None
    try:
        # Add city context from address (e.g. "123 Main St, Austin, TX" → "Austin")
        city = address.split(',')[1].strip() if address and address.count(',') >= 1 else ''
        query = f"{name} {city}".strip() if city else name
        r = requests.get(
            LOCAL_BIZ_SEARCH_URL,
            params={
                "query": query,
                "limit": "1",
                "extract_emails_and_contacts": "true",
                "language": "en",
                "region": "us",
            },
            headers={"x-api-key": owinja_key},
            timeout=15
        )
        if not r.ok:
            return None
        data = r.json()
        results = data.get("data", [])
        if not results:
            return None
        result = results[0]
        email = result.get("email")
        if not email:
            emails = result.get("emails", [])
            email = emails[0] if emails else None
        return email or None
    except Exception as e:
        logger.warning(f"OpenWebNinja local biz search failed for {name}: {e}")
    return None


def _get_yelp_data(name, address, owinja_key):
    """Look up a business on Yelp via OpenWebNinja — returns rating, review count, and URL."""
    if not name or not owinja_key:
        return None
    try:
        city = address.split(',')[1].strip() if address and address.count(',') >= 1 else ''
        query = f"{name} {city}".strip() if city else name
        r = requests.get(
            YELP_SEARCH_URL,
            params={"query": query, "limit": "1"},
            headers={"x-api-key": owinja_key},
            timeout=15
        )
        if not r.ok:
            return None
        data = r.json()
        results = data.get("data", [])
        if not results:
            return None
        biz = results[0]
        rating = biz.get("rating")
        review_count = biz.get("review_count")
        url = biz.get("url") or biz.get("yelp_url") or biz.get("link")
        if not rating:
            return None
        return {"rating": rating, "review_count": review_count, "url": url}
    except Exception as e:
        logger.warning(f"Yelp data fetch failed for {name}: {e}")
    return None


def _get_website_contacts(website, owinja_key):
    """Scrape a business website for contact emails via OpenWebNinja Website Contacts Scraper."""
    if not website or not owinja_key:
        return []
    try:
        r = requests.get(
            WEBSITE_CONTACTS_URL,
            params={"url": website},
            headers={"x-api-key": owinja_key},
            timeout=20
        )
        if not r.ok:
            return []
        data = r.json()
        contacts_raw = data.get("data", {}).get("contacts", []) or data.get("contacts", [])
        result = []
        seen = set()
        for c in contacts_raw:
            email = c.get("email") or c.get("email_address")
            if not email or email in seen:
                continue
            position = c.get("position") or c.get("title") or c.get("job_title") or ""
            if not is_senior(position):
                continue
            seen.add(email)
            result.append({
                "first_name": c.get("first_name", ""),
                "last_name": c.get("last_name", ""),
                "email": email,
                "position": position,
                "source": "website_scraper",
            })
        return result
    except Exception as e:
        logger.warning(f"Website contacts scraper failed for {website}: {e}")
    return []


def enrich_candidate(candidate, maps_key, prospeo_key, owinja_key=None, blitz_key=None, mv_key=None, openrouter_key=None):
    try:
        details = get_place_details(candidate["place_id"], maps_key)
        domain = extract_domain(details.get("website"))
        contacts, company_phone = get_domain_contacts(domain, blitz_key=blitz_key, prospeo_key=prospeo_key)
        if not contacts and owinja_key and details.get("website"):
            contacts = _get_website_contacts(details["website"], owinja_key)
        if mv_key and contacts:
            for c in contacts:
                if c.get("email") and not c.get("verification_status"):
                    c["verification_status"] = verify_email_mv(c["email"], mv_key)
        hours_data = details.get("opening_hours", {})
        clean_types = [t for t in details.get("types", []) if t not in NOISE_TYPES]
        name = details.get("name")
        news = get_company_news(name, owinja_key) if owinja_key else None
        ai_analysis = get_ai_analysis(name, domain, clean_types, openrouter_key) if openrouter_key else None
        google_phone = details.get("formatted_phone_number")
        address = details.get("formatted_address", "")
        business_email = _get_local_biz_email(name, address, owinja_key) if owinja_key else None
        yelp = _get_yelp_data(name, address, owinja_key) if owinja_key else None
        return {
            "name": name,
            "address": address,
            "phone": google_phone or company_phone,
            "website": details.get("website"),
            "domain": domain,
            "rating": details.get("rating"),
            "total_ratings": details.get("user_ratings_total"),
            "business_status": details.get("business_status"),
            "types": clean_types,
            "open_now": hours_data.get("open_now"),
            "hours": hours_data.get("weekday_text", []),
            "place_id": candidate["place_id"],
            "contacts": contacts,
            "business_email": business_email,
            "yelp": yelp,
            "google_rank": candidate.get("google_rank"),
            "recent_news": news,
            "ai_analysis": ai_analysis,
        }
    except Exception as e:
        logger.error(f"Failed to enrich {candidate.get('place_id')}: {e}")
        return None


def run_leads_search(business_type, location, limit, maps_key, prospeo_key, owinja_key=None, blitz_key=None, mv_key=None, openrouter_key=None):
    query = f"{business_type} in {location}"
    candidates = get_place_candidates(query, maps_key)[:min(limit, 20)]
    for i, c in enumerate(candidates):
        c["google_rank"] = i + 1

    leads = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(enrich_candidate, c, maps_key, prospeo_key, owinja_key, blitz_key, mv_key, openrouter_key): c
            for c in candidates
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                leads.append(result)

    leads.sort(key=lambda x: (x.get("rating") or 0), reverse=True)

    return {
        "leads": leads,
        "total": len(leads),
        "contacts_found": sum(1 for l in leads if l.get("contacts")),
        "query": query
    }
