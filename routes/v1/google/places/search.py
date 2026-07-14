from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
import logging
import os
import requests

v1_google_places_search_bp = Blueprint('v1_google_places_search', __name__)
logger = logging.getLogger(__name__)

PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

DETAIL_FIELDS = "name,formatted_address,formatted_phone_number,website,opening_hours,rating,user_ratings_total,business_status,types"

@v1_google_places_search_bp.route('/v1/google/places/search', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "location": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["query"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def search_places(job_id, data):
    query = data['query']
    location = data.get('location')

    logger.info(f"Job {job_id}: Searching Google Places for '{query}'")

    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return "GOOGLE_MAPS_API_KEY is not configured", "/v1/google/places/search", 500

    try:
        params = {"query": query, "key": api_key}
        if location:
            params["location"] = location

        search_response = requests.get(PLACES_SEARCH_URL, params=params, timeout=30)
        search_response.raise_for_status()
        search_data = search_response.json()

        if search_data.get("status") not in ("OK", "ZERO_RESULTS"):
            return f"Google Places error: {search_data.get('status')} - {search_data.get('error_message', '')}", "/v1/google/places/search", 400

        places = []
        for candidate in search_data.get("results", [])[:5]:
            place_id = candidate.get("place_id")
            detail_response = requests.get(
                PLACES_DETAILS_URL,
                params={"place_id": place_id, "fields": DETAIL_FIELDS, "key": api_key},
                timeout=30
            )
            detail_response.raise_for_status()
            detail_data = detail_response.json().get("result", {})

            hours = detail_data.get("opening_hours", {})
            places.append({
                "name": detail_data.get("name"),
                "address": detail_data.get("formatted_address"),
                "phone": detail_data.get("formatted_phone_number"),
                "website": detail_data.get("website"),
                "rating": detail_data.get("rating"),
                "total_ratings": detail_data.get("user_ratings_total"),
                "business_status": detail_data.get("business_status"),
                "types": detail_data.get("types", []),
                "open_now": hours.get("open_now"),
                "hours": hours.get("weekday_text", []),
                "place_id": place_id
            })

        return {"results": places, "total": len(places)}, "/v1/google/places/search", 200

    except requests.exceptions.HTTPError as e:
        logger.error(f"Job {job_id}: Google Places HTTP error - {str(e)}")
        return str(e), "/v1/google/places/search", 500
    except Exception as e:
        logger.error(f"Job {job_id}: Google Places search failed - {str(e)}")
        return str(e), "/v1/google/places/search", 500
