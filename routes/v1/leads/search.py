from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.leads_service import run_leads_search
import logging
import os

v1_leads_search_bp = Blueprint('v1_leads_search', __name__)
logger = logging.getLogger(__name__)


@v1_leads_search_bp.route('/v1/leads/search', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "business_type": {"type": "string"},
        "location": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 20},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["business_type", "location"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def search_leads(job_id, data):
    business_type = data['business_type']
    location = data['location']
    limit = min(data.get('limit', 10), 20)

    maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    prospeo_key = os.environ.get('PROSPEO_API_KEY')

    if not maps_key:
        return "GOOGLE_MAPS_API_KEY is not configured", "/v1/leads/search", 500

    logger.info(f"Job {job_id}: Lead search — {limit}x {business_type} in {location}")

    try:
        result = run_leads_search(business_type, location, limit, maps_key, prospeo_key)
        return result, "/v1/leads/search", 200
    except ValueError as e:
        return str(e), "/v1/leads/search", 400
    except Exception as e:
        logger.error(f"Job {job_id}: Lead search failed — {e}")
        return str(e), "/v1/leads/search", 500
