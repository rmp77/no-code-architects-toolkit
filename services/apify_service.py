import requests
import logging

logger = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"
INSTAGRAM_ACTOR = "easy_scraper~instagram-leads-scraper"
B2B_ACTOR = "code_crafter~leads-finder"


def _run_actor(actor_id, payload, api_token, wait=120):
    """Start an Apify actor run synchronously (waitForFinish). Returns raw items list."""
    url = f"{APIFY_BASE}/acts/{actor_id}/runs"
    params = {"token": api_token, "waitForFinish": wait}

    r = requests.post(url, json=payload, params=params, timeout=wait + 60)
    r.raise_for_status()
    run = r.json().get("data", {})

    status = run.get("status", "")
    if status not in ("SUCCEEDED", "FINISHED", "READY", "RUNNING"):
        msg = run.get("statusMessage") or run.get("message") or status
        raise ValueError(f"Apify actor ended with status '{status}': {msg}")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise ValueError("Apify run returned no dataset ID")

    items_r = requests.get(
        f"{APIFY_BASE}/datasets/{dataset_id}/items",
        params={"token": api_token, "format": "json"},
        timeout=30
    )
    items_r.raise_for_status()
    return items_r.json() or []


def _normalize_instagram(item):
    """Map Instagram scraper output fields to our standard lead dict."""
    username = item.get("username") or item.get("handle") or ""
    full_name = (item.get("fullName") or item.get("full_name") or
                 item.get("name") or username)
    bio = (item.get("biography") or item.get("bio") or
           item.get("description") or "")
    email = (item.get("businessEmail") or item.get("business_email") or
             item.get("email") or "")
    phone = (item.get("businessPhone") or item.get("business_phone") or
             item.get("phone") or "")
    followers = (item.get("followersCount") or item.get("followers_count") or
                 item.get("followers") or 0)
    profile_url = (item.get("url") or item.get("profileUrl") or
                   (f"https://www.instagram.com/{username}/" if username else ""))
    website = (item.get("externalUrl") or item.get("external_url") or
               item.get("website") or item.get("websiteUrl") or "")

    contacts = []
    if full_name and email:
        parts = full_name.strip().split(" ", 1)
        contacts.append({
            "first_name": parts[0],
            "last_name": parts[1] if len(parts) > 1 else "",
            "email": email,
            "position": "Instagram Profile",
            "source": "instagram",
        })

    return {
        "name": full_name or username or "Unknown",
        "username": username,
        "profile_url": profile_url,
        "bio": bio,
        "followers": followers,
        "phone": phone,
        "website": website,
        "email": email,
        "contacts": contacts,
        "source": "instagram",
    }


def _normalize_b2b(item):
    """Map B2B leads finder output fields to our standard lead dict."""
    company = (item.get("company") or item.get("companyName") or
               item.get("company_name") or item.get("organization") or
               item.get("name") or "Unknown")
    first_name = (item.get("firstName") or item.get("first_name") or
                  item.get("given_name") or "")
    last_name = (item.get("lastName") or item.get("last_name") or
                 item.get("family_name") or "")
    full_name = (item.get("fullName") or item.get("full_name") or
                 f"{first_name} {last_name}".strip())
    email = (item.get("email") or item.get("emailAddress") or
             item.get("email_address") or "")
    phone = (item.get("phone") or item.get("phoneNumber") or
             item.get("phone_number") or item.get("mobilePhone") or "")
    title = (item.get("title") or item.get("jobTitle") or item.get("job_title") or
             item.get("position") or "")
    website = (item.get("website") or item.get("companyWebsite") or
               item.get("company_website") or item.get("domain") or "")
    address = (item.get("address") or item.get("location") or
               item.get("city") or "")
    linkedin = (item.get("linkedinUrl") or item.get("linkedin_url") or
                item.get("linkedin") or "")

    contacts = []
    if full_name or email or phone:
        parts = (full_name or "").strip().split(" ", 1)
        contacts.append({
            "first_name": first_name or (parts[0] if parts else ""),
            "last_name": last_name or (parts[1] if len(parts) > 1 else ""),
            "email": email,
            "position": title,
            "linkedin_url": linkedin,
            "source": "b2b_finder",
        })

    return {
        "name": company,
        "phone": phone,
        "website": website,
        "address": address,
        "contacts": contacts,
        "source": "b2b_finder",
    }


def run_instagram_scraper(hashtags, limit, api_token):
    """
    Scrape Instagram profiles by hashtags.
    hashtags: list of strings or comma-separated string.
    Returns standard leads dict.
    """
    if isinstance(hashtags, str):
        hashtags = [t.strip() for t in hashtags.split(",") if t.strip()]
    clean = [f"#{t.lstrip('#')}" for t in hashtags if t.strip()]
    if not clean:
        raise ValueError("At least one hashtag is required")

    payload = {
        "hashtags": clean,
        "resultsLimit": min(limit, 100),
        "maxItems": min(limit, 100),
    }
    logger.info(f"Apify Instagram scraper: hashtags={clean}, limit={limit}")
    items = _run_actor(INSTAGRAM_ACTOR, payload, api_token)
    leads = [_normalize_instagram(item) for item in items if item]

    return {
        "leads": leads,
        "total": len(leads),
        "contacts_found": sum(1 for l in leads if l.get("email") or l.get("contacts")),
        "query": f"Instagram: {', '.join(clean)}",
    }


def run_b2b_finder(query, location, limit, api_token):
    """
    Find B2B leads by job title / role and optional location.
    Returns standard leads dict.
    """
    payload = {
        "searchQuery": query,
        "location": location,
        "maxResults": min(limit, 100),
        "keyword": query,
        "query": query,
        "limit": min(limit, 100),
    }
    logger.info(f"Apify B2B finder: query='{query}', location='{location}', limit={limit}")
    items = _run_actor(B2B_ACTOR, payload, api_token)
    leads = [_normalize_b2b(item) for item in items if item]

    loc_part = f" in {location}" if location else ""
    return {
        "leads": leads,
        "total": len(leads),
        "contacts_found": sum(1 for l in leads if l.get("contacts")),
        "query": f"B2B: {query}{loc_part}",
    }
