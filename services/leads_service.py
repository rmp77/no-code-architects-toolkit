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

NEWS_BLOCKLIST = ["obituary", "wikipedia", "jobs.", "careers.", "lawsuit", "indictment"]

SENIOR_KEYWORDS = [
    "owner", "founder", "ceo", "president", "coo", "cto", "cfo",
    "director", "manager", "principal", "partner", "vp",
    "vice president", "head of", "chief", "proprietor", "operator", "managing"
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


def get_domain_contacts(domain, api_key):
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
            "confidence_score": c.get("confidence_score")
        } for c in seniors]
    except Exception as e:
        logger.warning(f"Prospeo domain search failed for {domain}: {e}")
        return []


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


def enrich_candidate(candidate, maps_key, prospeo_key, owinja_key=None):
    try:
        details = get_place_details(candidate["place_id"], maps_key)
        domain = extract_domain(details.get("website"))
        contacts = get_domain_contacts(domain, prospeo_key)
        hours_data = details.get("opening_hours", {})
        clean_types = [t for t in details.get("types", []) if t not in NOISE_TYPES]
        name = details.get("name")
        news = get_company_news(name, owinja_key) if owinja_key else None
        return {
            "name": name,
            "address": details.get("formatted_address"),
            "phone": details.get("formatted_phone_number"),
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
            "recent_news": news,
        }
    except Exception as e:
        logger.error(f"Failed to enrich {candidate.get('place_id')}: {e}")
        return None


def run_leads_search(business_type, location, limit, maps_key, prospeo_key, owinja_key=None):
    query = f"{business_type} in {location}"
    candidates = get_place_candidates(query, maps_key)[:min(limit, 20)]

    leads = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(enrich_candidate, c, maps_key, prospeo_key, owinja_key): c for c in candidates}
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
