from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.v1.social.blotato_service import list_posts
import logging
import os

v1_social_posts_bp = Blueprint('v1_social_posts', __name__)
logger = logging.getLogger(__name__)

PLATFORMS = ['twitter', 'facebook', 'instagram', 'linkedin', 'tiktok', 'pinterest', 'threads', 'bluesky', 'youtube']
STATUSES = ['scheduled', 'published', 'failed']


@v1_social_posts_bp.route('/v1/social/posts', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "since": {"type": "string"},
        "until": {"type": "string"},
        "status": {
            "oneOf": [
                {"type": "string", "enum": STATUSES},
                {"type": "array", "items": {"type": "string", "enum": STATUSES}}
            ]
        },
        "platform": {
            "oneOf": [
                {"type": "string", "enum": PLATFORMS},
                {"type": "array", "items": {"type": "string", "enum": PLATFORMS}}
            ]
        },
        "limit": {"type": "integer", "minimum": 1, "maximum": 250},
        "cursor": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def list_social_posts(job_id, data):
    logger.info(f"Job {job_id}: Listing social posts")

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/posts", 500

    try:
        result = list_posts(
            since=data.get('since'),
            until=data.get('until'),
            status=data.get('status'),
            platform=data.get('platform'),
            limit=data.get('limit', 50),
            cursor=data.get('cursor'),
        )
        return result, "/v1/social/posts", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to list posts — {e}")
        return str(e), "/v1/social/posts", 500
