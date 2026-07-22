from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.v1.social.blotato_service import list_schedules, delete_schedule, update_schedule
import logging
import os

v1_social_schedules_bp = Blueprint('v1_social_schedules', __name__)
logger = logging.getLogger(__name__)


@v1_social_schedules_bp.route('/v1/social/schedules', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
        "cursor": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def list_social_schedules(job_id, data):
    logger.info(f"Job {job_id}: Listing social schedules")

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/schedules", 500

    try:
        result = list_schedules(limit=data.get('limit', 20), cursor=data.get('cursor'))
        return result, "/v1/social/schedules", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to list schedules — {e}")
        return str(e), "/v1/social/schedules", 500


@v1_social_schedules_bp.route('/v1/social/schedules/delete', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "schedule_id": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["schedule_id"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def delete_social_schedule(job_id, data):
    schedule_id = data["schedule_id"]
    logger.info(f"Job {job_id}: Deleting schedule {schedule_id}")

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/schedules/delete", 500

    try:
        result = delete_schedule(schedule_id)
        return result or {"ok": True}, "/v1/social/schedules/delete", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to delete schedule — {e}")
        return str(e), "/v1/social/schedules/delete", 500


@v1_social_schedules_bp.route('/v1/social/schedules/update', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "schedule_id": {"type": "string"},
        "scheduled_time": {"type": "string"},
        "text": {"type": "string"},
        "media_urls": {"type": "array", "items": {"type": "string"}},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["schedule_id"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def update_social_schedule(job_id, data):
    schedule_id = data["schedule_id"]
    logger.info(f"Job {job_id}: Updating schedule {schedule_id}")

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/schedules/update", 500

    payload = {}
    if data.get("scheduled_time"):
        payload["scheduledTime"] = data["scheduled_time"]
    if data.get("text") is not None:
        payload["text"] = data["text"]
    if data.get("media_urls") is not None:
        payload["mediaUrls"] = data["media_urls"]

    try:
        result = update_schedule(schedule_id, payload)
        return result, "/v1/social/schedules/update", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to update schedule — {e}")
        return str(e), "/v1/social/schedules/update", 500
