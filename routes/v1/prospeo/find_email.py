from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
import logging
import os
import requests

v1_prospeo_find_email_bp = Blueprint('v1_prospeo_find_email', __name__)
logger = logging.getLogger(__name__)

PROSPEO_API_URL = "https://api.prospeo.io/email-finder"

@v1_prospeo_find_email_bp.route('/v1/prospeo/find_email', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "domain": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["first_name", "last_name", "domain"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def find_email(job_id, data):
    first_name = data['first_name']
    last_name = data['last_name']
    domain = data['domain']

    logger.info(f"Job {job_id}: Looking up email for {first_name} {last_name} at {domain}")

    api_key = os.environ.get('PROSPEO_API_KEY')
    if not api_key:
        return "PROSPEO_API_KEY is not configured", "/v1/prospeo/find_email", 500

    try:
        response = requests.post(
            PROSPEO_API_URL,
            json={"first_name": first_name, "last_name": last_name, "domain": domain},
            headers={"X-KEY": api_key, "Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("error") is False and result.get("error"):
            return result.get("message", "Prospeo API error"), "/v1/prospeo/find_email", 400

        email_data = result.get("response", {})
        return {
            "email": email_data.get("email"),
            "verification_status": email_data.get("verification_status"),
            "confidence_score": email_data.get("confidence_score"),
            "first_name": first_name,
            "last_name": last_name,
            "domain": domain
        }, "/v1/prospeo/find_email", 200

    except requests.exceptions.HTTPError as e:
        logger.error(f"Job {job_id}: Prospeo API HTTP error - {str(e)}")
        return str(e), "/v1/prospeo/find_email", 500
    except Exception as e:
        logger.error(f"Job {job_id}: Prospeo lookup failed - {str(e)}")
        return str(e), "/v1/prospeo/find_email", 500
