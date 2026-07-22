from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.v1.social.blotato_service import create_post, get_post_status
import logging
import os

v1_social_post_bp = Blueprint('v1_social_post', __name__)
logger = logging.getLogger(__name__)


@v1_social_post_bp.route('/v1/social/post/create', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "account_id": {"type": "string"},
        "platform": {"type": "string"},
        "text": {"type": "string"},
        "media_urls": {"type": "array", "items": {"type": "string"}},
        "scheduled_time": {"type": "string"},
        "use_next_free_slot": {"type": "boolean"},
        "additional_posts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "media_urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["text"]
            }
        },
        "page_id": {"type": "string"},
        "media_type": {"type": "string"},
        "privacy_level": {"type": "string", "enum": ["SELF_ONLY", "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR"]},
        "privacy_status": {"type": "string", "enum": ["public", "private", "unlisted"]},
        "title": {"type": "string"},
        "board_id": {"type": "string"},
        "reply_control": {"type": "string", "enum": ["everyone", "accounts_you_follow", "mentioned_only"]},
        "alt_text": {"type": "string"},
        "link": {"type": "string"},
        "collaborators": {"type": "array", "items": {"type": "string"}},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["account_id", "platform", "text"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def create_social_post(job_id, data):
    logger.info(f"Job {job_id}: Creating social post on {data.get('platform')}")

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/post/create", 500

    payload = {
        "accountId": data["account_id"],
        "platform": data["platform"],
        "text": data["text"],
        "mediaUrls": data.get("media_urls", []),
    }

    optional = {
        "scheduled_time": "scheduledTime",
        "use_next_free_slot": "useNextFreeSlot",
        "page_id": "pageId",
        "media_type": "mediaType",
        "privacy_level": "privacyLevel",
        "privacy_status": "privacyStatus",
        "title": "title",
        "board_id": "boardId",
        "reply_control": "replyControl",
        "alt_text": "altText",
        "link": "link",
        "collaborators": "collaborators",
    }
    for src, dst in optional.items():
        if data.get(src) is not None:
            payload[dst] = data[src]

    if data.get("additional_posts"):
        payload["additionalPosts"] = [
            {"text": p["text"], "mediaUrls": p.get("media_urls", [])}
            for p in data["additional_posts"]
        ]

    try:
        result = create_post(payload)
        return result, "/v1/social/post/create", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to create post — {e}")
        return str(e), "/v1/social/post/create", 500


@v1_social_post_bp.route('/v1/social/post/status', methods=['POST'])
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
def get_social_post_status(job_id, data):
    post_id = data["post_id"]
    logger.info(f"Job {job_id}: Getting status for post {post_id}")

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/post/status", 500

    try:
        result = get_post_status(post_id)
        return result, "/v1/social/post/status", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to get post status — {e}")
        return str(e), "/v1/social/post/status", 500
