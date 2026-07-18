from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
import logging
import os
import requests
from urllib.parse import urlparse

v1_leads_lookup_bp = Blueprint('v1_leads_lookup', __name__)
logger = logging.getLogger(__name__)

PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACES_DETAIL_FIELDS = "name,formatted_address,formatted_phone_number,website,opening_hours,rating,user_ratings_total,business_status,types"
PROSPEO_API_URL = "https://api.prospeo.io/email-finder"

def _extract_domain(website_url):
    if not website_url:
        return None
    parsed = urlparse(website_url)
    host = parsed.netloc or parsed.path
    return host.removeprefix("www.")

def _search_place(query, api_key):
    response = requests.get(
        PLACES_SEARCH_URL,
        params={"query": query, "key": api_key},
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise ValueError(f"Google Places error: {data.get('status')} - {data.get('error_message', '')}")
    results = data.get("results", [])
    return results[0] if results else None

def _get_place_details(place_id, api_key):
    response = requests.get(
        PLACES_DETAILS_URL,
        params={"place_id": place_id, "fields": PLACES_DETAIL_FIELDS, "key": api_key},
        timeout=30
    )
    response.raise_for_status()
    return response.json().get("result", {})

def _find_email(first_name, last_name, domain, api_key):
    response = requests.post(
        PROSPEO_API_URL,
        json={"first_name": first_name, "last_name": last_name, "domain": domain},
        headers={"X-KEY": api_key, "Content-Type": "application/json"},
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    email_data = result.get("response", {})
    return {
        "email": email_data.get("email"),
        "verification_status": email_data.get("verification_status"),
        "confidence_score": email_data.get("confidence_score")
    }

@v1_leads_lookup_bp.route('/v1/leads/lookup', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "business_query": {"type": "string"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["business_query", "first_name", "last_name"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def lookup_lead(job_id, data):
    business_query = data['business_query']
    first_name = data['first_name']
    last_name = data['last_name']

    logger.info(f"Job {job_id}: Lead lookup for {first_name} {last_name} at '{business_query}'")

    maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    prospeo_key = os.environ.get('PROSPEO_API_KEY')

    if not maps_key:
        return "GOOGLE_MAPS_API_KEY is not configured", "/v1/leads/lookup", 500
    if not prospeo_key:
        return "PROSPEO_API_KEY is not configured", "/v1/leads/lookup", 500

    try:
        candidate = _search_place(business_query, maps_key)
        if not candidate:
            return {"found": False, "business_query": business_query}, "/v1/leads/lookup", 200

        details = _get_place_details(candidate["place_id"], maps_key)

        hours = details.get("opening_hours", {})
        business = {
            "name": details.get("name"),
            "address": details.get("formatted_address"),
            "phone": details.get("formatted_phone_number"),
            "website": details.get("website"),
            "rating": details.get("rating"),
            "total_ratings": details.get("user_ratings_total"),
            "business_status": details.get("business_status"),
            "types": details.get("types", []),
            "open_now": hours.get("open_now"),
            "hours": hours.get("weekday_text", []),
            "place_id": candidate["place_id"]
        }

        domain = _extract_domain(details.get("website"))
        contact = {"first_name": first_name, "last_name": last_name, "domain": domain}

        if domain:
            try:
                email_result = _find_email(first_name, last_name, domain, prospeo_key)
                contact.update(email_result)
            except Exception as e:
                logger.warning(f"Job {job_id}: Prospeo lookup failed for {domain} - {str(e)}")
                contact["email"] = None
                contact["email_error"] = str(e)
        else:
            contact["email"] = None
            contact["email_error"] = "No website found on Google Maps — cannot determine domain"

        return {
            "found": True,
            "business": business,
            "contact": contact
        }, "/v1/leads/lookup", 200

    except ValueError as e:
        return str(e), "/v1/leads/lookup", 400
    except Exception as e:
        logger.error(f"Job {job_id}: Lead lookup failed - {str(e)}")
        return str(e), "/v1/leads/lookup", 500
