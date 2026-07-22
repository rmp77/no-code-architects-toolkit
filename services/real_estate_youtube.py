import os
import re
import logging
import requests
import json
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("RE_AI_MODEL", "openai/gpt-4o-mini")
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# Zillow property detail scraper via OpenWebNinja
OPENWEBNINJA_URL = "https://api.openwebninja.com/real-time-web-search/search"


def scrape_zillow_property(zillow_url: str) -> dict:
    """Extract property data from a Zillow URL using search context."""
    api_key = os.environ.get("OPENWEBNINJA_KEY")
    if not api_key:
        return {"error": "OPENWEBNINJA_KEY not configured", "url": zillow_url}

    # Extract address from Zillow URL path: /homedetails/123-main-st.../zpid
    path = urlparse(zillow_url).path
    address_slug = ""
    m = re.search(r"/homedetails/([^/]+)/", path)
    if m:
        address_slug = m.group(1).replace("-", " ")

    search_query = f"site:zillow.com {address_slug or zillow_url}"
    try:
        resp = requests.get(
            OPENWEBNINJA_URL,
            params={"api_key": api_key, "query": search_query, "limit": 1},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", [])
        return {
            "address": address_slug.title(),
            "zillow_url": zillow_url,
            "snippet": results[0].get("description", "") if results else "",
            "title": results[0].get("title", "") if results else "",
        }
    except Exception as e:
        logger.error(f"Zillow scrape error: {e}")
        return {"address": address_slug.title(), "zillow_url": zillow_url}


def generate_video_script(property_data: dict, tracking_phone: str) -> dict:
    """Use AI to generate a YouTube video script and title for a property."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return _fallback_script(property_data, tracking_phone)

    prompt = f"""Create a YouTube real estate video script for Deal Flow Direct in San Diego.

Property: {json.dumps(property_data)}
Tracking phone: {tracking_phone}

Rules:
- 60-90 second script (slideshow style — narration over property photos)
- Hook in first 5 seconds (don't start with "In this video...")
- Highlight: price/deal angle, location, key features, investment potential
- End with strong CTA to call {tracking_phone}
- YouTube title: SEO-optimized, under 70 chars, include "San Diego" and property type
- YouTube description: 150 words with phone number prominent, keywords at bottom

Return ONLY valid JSON:
{{
  "title": "...",
  "script": "full narration script",
  "description": "youtube description",
  "tags": ["tag1", "tag2", ...],
  "thumbnail_text": "text overlay for thumbnail"
}}"""

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 800,
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Script generation error: {e}")
        return _fallback_script(property_data, tracking_phone)


def get_invideo_automation_config(property_data: dict, script: dict, tracking_phone: str) -> dict:
    """Return a Make.com / InVideo automation configuration payload."""
    return {
        "invideo_config": {
            "template": "real_estate_slideshow",
            "title": script.get("title", ""),
            "script": script.get("script", ""),
            "outro_text": f"Call {tracking_phone} — Deal Flow Direct",
            "brand_colors": {"primary": "#1B2A5E", "accent": "#F5B800"},
            "image_sources": ["zillow", "google_street_view"],
            "duration_target_seconds": 75,
        },
        "youtube_config": {
            "title": script.get("title", ""),
            "description": script.get("description", ""),
            "tags": script.get("tags", []),
            "category_id": "37",  # Real Estate
            "privacy": "public",
            "made_for_kids": False,
        },
        "make_webhook_notes": (
            "1. Trigger: new row in Airtable/Google Sheets with Zillow URL\n"
            "2. HTTP GET: scrape property via /v1/real_estate/youtube/prepare\n"
            "3. InVideo API: create video with config above\n"
            "4. YouTube Data API v3: upload with youtube_config\n"
            "5. POST result back to /v1/real_estate/youtube/complete with video_id"
        ),
    }


def _fallback_script(property_data: dict, tracking_phone: str) -> dict:
    addr = property_data.get("address", "San Diego Property")
    return {
        "title": f"OFF MARKET Deal in San Diego — {addr[:40]}",
        "script": (
            f"Stop scrolling — this one's different. "
            f"We just got an off-market property in {addr} that won't last. "
            f"No MLS, no bidding wars, no wasted weekends at open houses. "
            f"Deal Flow Direct sources motivated sellers directly so you get the deal FIRST. "
            f"If you're a cash buyer or investor in the San Diego market, "
            f"call us right now at {tracking_phone}. "
            f"Serious buyers only — these deals move fast."
        ),
        "description": (
            f"Off-market real estate deal in San Diego — {addr}.\n\n"
            f"Deal Flow Direct connects cash buyers and investors with motivated sellers "
            f"before properties hit the MLS. Get first access to distressed properties, "
            f"foreclosures, and estate sales in San Diego County.\n\n"
            f"📞 Call or text: {tracking_phone}\n\n"
            f"#SanDiegoRealEstate #OffMarket #CashBuyer #WholesaleRealEstate #InvestmentProperty"
        ),
        "tags": ["San Diego real estate", "off market", "cash buyer", "wholesale", "investment property", "motivated seller"],
        "thumbnail_text": f"OFF MARKET\n{addr[:30]}\nCall {tracking_phone}",
    }
