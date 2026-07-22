from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.v1.social.blotato_service import get_post_analytics
import logging
import os

v1_social_analytics_bp = Blueprint('v1_social_analytics', __name__)
logger = logging.getLogger(__name__)


@v1_social_analytics_bp.route('/v1/social/analytics', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "post_id": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["post_id"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def get_social_analytics(job_id, data):
    post_id = data["post_id"]
    logger.info(f"Job {job_id}: Getting analytics for post {post_id}")

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/analytics", 500

    try:
        result = get_post_analytics(post_id)
        return result, "/v1/social/analytics", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to get analytics — {e}")
        return str(e), "/v1/social/analytics", 500
