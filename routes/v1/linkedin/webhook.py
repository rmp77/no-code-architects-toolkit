from flask import Blueprint, request, jsonify
from app_utils import validate_payload
from services.authentication import authenticate
from services.linkedin_service import handle_oxoray_event
import logging

v1_linkedin_webhook_bp = Blueprint('v1_linkedin_webhook', __name__)
logger = logging.getLogger(__name__)


@v1_linkedin_webhook_bp.route('/v1/linkedin/webhook', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "event_type": {
            "type": "string",
            "enum": ["prospect_qualified", "meeting_booked", "prospect_silent", "prospect_replied", "prospect_disqualified"]
        },
        "prospect": {
            "type": "object",
            "properties": {
                "linkedin_url": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "city": {"type": "string"},
                "title": {"type": "string"},
                "email": {"type": "string"},
                "archetype": {"type": "string", "enum": ["grinder", "operator", "scaler", "unknown"]}
            },
            "required": ["linkedin_url", "first_name"]
        },
        "campaign_id": {"type": "string"},
        "meeting_url": {"type": "string"},
        "notes": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["event_type", "prospect"],
    "additionalProperties": False
})
def linkedin_webhook():
    data = request.get_json(force=True)
    event_type = data.get("event_type")
    prospect = data.get("prospect", {})

    logger.info(f"OXORAY webhook received — event={event_type} prospect={prospect.get('first_name')} {prospect.get('last_name')}")

    try:
        result = handle_oxoray_event(event_type, prospect, data)
        return jsonify({
            "code": 200,
            "message": "event processed",
            "result": result
        }), 200
    except Exception as e:
        logger.error(f"LinkedIn webhook error: {e}")
        return jsonify({
            "code": 500,
            "message": str(e)
        }), 500
