from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from services.v1.social.blotato_service import list_accounts
import logging
import os

v1_social_accounts_bp = Blueprint('v1_social_accounts', __name__)
logger = logging.getLogger(__name__)

PLATFORMS = ['twitter', 'facebook', 'instagram', 'linkedin', 'tiktok', 'pinterest', 'threads', 'bluesky', 'youtube']


@v1_social_accounts_bp.route('/v1/social/accounts', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "platform": {"type": "string", "enum": PLATFORMS},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)
def get_social_accounts(job_id, data):
    platform = data.get('platform')
    logger.info(f"Job {job_id}: Listing social accounts" + (f" for {platform}" if platform else ""))

    if not os.environ.get('BLOTATO_API_KEY'):
        return "BLOTATO_API_KEY is not configured", "/v1/social/accounts", 500

    try:
        result = list_accounts(platform=platform)
        return result, "/v1/social/accounts", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Failed to list accounts — {e}")
        return str(e), "/v1/social/accounts", 500
