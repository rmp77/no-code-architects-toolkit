import requests
import logging

logger = logging.getLogger(__name__)

REACHINBOX_API = "https://api.reachinbox.ai/api/v1"


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_campaigns(api_key):
    """Returns list of campaigns: [{id, name, status}]"""
    r = requests.get(f"{REACHINBOX_API}/campaigns", headers=_headers(api_key), timeout=15)
    r.raise_for_status()
    data = r.json()
    campaigns = data.get("data", data) if isinstance(data, dict) else data
    return [
        {
            "id": str(c.get("id", "")),
            "name": c.get("name", "Unnamed"),
            "status": c.get("status", ""),
        }
        for c in (campaigns if isinstance(campaigns, list) else [])
    ]


def _extract_city(address):
    """Pull city from a formatted address string like '123 Main St, Tampa, FL 33601, USA'."""
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    # Typically: [street, city, state+zip, country]
    return parts[1] if len(parts) >= 3 else parts[0]


def _build_lead_payload(lead):
    """
    Convert a dashboard lead dict into a flat ReachInbox contact payload
    with all PRISM research variables pre-populated for personalized sequences.

    Stage 1 variables (PRISM — business owner outreach):
      googleRank, googleRating, totalRatings, yelpRating, yelpReviewCount,
      yelpGap, city, businessType, coldEmailAngle, businessCategory,
      businessSummary, customerType, recentNewsTitle, recentNewsUrl

    Stage 2+ variables (ultimate client / 18-question / 5-question frameworks)
    can be appended here as the sequences are built out.
    """
    contacts = lead.get("contacts") or []
    primary = contacts[0] if contacts else {}
    email = primary.get("email") or lead.get("business_email") or ""
    if not email:
        return None

    ai = lead.get("ai_analysis") or {}
    yelp = lead.get("yelp") or {}
    news = lead.get("recent_news") or {}
    address = lead.get("address", "")
    city = _extract_city(address)

    google_rating = lead.get("rating") or ""
    yelp_rating = yelp.get("rating") or ""
    yelp_gap = ""
    if google_rating and yelp_rating:
        gap = round(float(google_rating) - float(yelp_rating), 1)
        yelp_gap = str(gap) if gap > 0 else ""

    business_types = lead.get("types") or []
    business_type = business_types[0].replace("_", " ").title() if business_types else ""

    return {
        # ── Core contact fields ──────────────────────────────────────────
        "email":        email,
        "firstName":    primary.get("first_name", "") or "",
        "lastName":     primary.get("last_name", "") or "",
        "companyName":  lead.get("name", ""),
        "phone":        lead.get("phone", ""),
        "website":      lead.get("website", ""),

        # ── PRISM Stage 1: Google Maps intelligence ──────────────────────
        "googleRank":       str(lead.get("google_rank", "")),
        "googleRating":     str(google_rating),
        "totalRatings":     str(lead.get("total_ratings", "")),
        "city":             city,
        "address":          address,
        "businessType":     business_type,
        "businessStatus":   lead.get("business_status", ""),

        # ── PRISM Stage 1: Yelp intelligence (conversation starter) ─────
        "yelpRating":       str(yelp_rating),
        "yelpReviewCount":  str(yelp.get("review_count", "")),
        "yelpGap":          yelp_gap,          # e.g. "1.5" stars lower than Google
        "yelpUrl":          yelp.get("url", ""),

        # ── PRISM Stage 1: AI-generated angles ──────────────────────────
        "coldEmailAngle":   ai.get("cold_email_angle", ""),
        "businessCategory": ai.get("category", ""),
        "businessSummary":  ai.get("summary", ""),
        "customerType":     ai.get("customer_type", ""),

        # ── PRISM Stage 1: Recent news hook ─────────────────────────────
        "recentNewsTitle":  news.get("title", ""),
        "recentNewsUrl":    news.get("url", ""),
        "recentNewsSnippet":news.get("snippet", ""),

        # ── Stage 2+ placeholders (18-question / 5-question framework) ──
        # Add new variables here as the ultimate-client sequences are built.
    }


def add_leads_to_campaign(campaign_id, leads, api_key):
    """
    Push a list of lead dicts into a ReachInbox campaign with full PRISM
    research variables so email templates can personalize at every stage.
    Returns (added_count, duplicate_count, errors[]).
    """
    payload_leads = []
    for lead in leads:
        entry = _build_lead_payload(lead)
        if entry:
            payload_leads.append(entry)

    if not payload_leads:
        return 0, 0, ["No leads with verified emails to push"]

    # All custom keys beyond the ReachInbox core set must be declared here
    custom_vars = [
        "googleRank", "googleRating", "totalRatings", "city", "address",
        "businessType", "businessStatus",
        "yelpRating", "yelpReviewCount", "yelpGap", "yelpUrl",
        "coldEmailAngle", "businessCategory", "businessSummary", "customerType",
        "recentNewsTitle", "recentNewsUrl", "recentNewsSnippet",
    ]

    payload = {
        "campaignId": str(campaign_id),
        "leads": payload_leads,
        "newCoreVariables": ["firstName", "lastName", "companyName", "phone", "website"] + custom_vars,
        "duplicates": [],
    }

    r = requests.post(
        f"{REACHINBOX_API}/leads/add",
        json=payload,
        headers=_headers(api_key),
        timeout=30,
    )
    r.raise_for_status()
    result = r.json()

    added = len(payload_leads)
    duplicates = len(result.get("duplicates", []))
    return added - duplicates, duplicates, []
