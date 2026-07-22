from flask import Blueprint, request, jsonify, Response
from services.v1.social.blotato_service import (
    list_accounts, create_post, list_posts,
    list_schedules, delete_schedule, update_schedule, get_post_analytics,
)
import logging
import os

social_dashboard_bp = Blueprint('social_dashboard', __name__)
logger = logging.getLogger(__name__)


@social_dashboard_bp.before_request
def require_auth():
    password = os.environ.get('DASHBOARD_PASSWORD', '')
    if not password:
        return None
    auth = request.authorization
    expected_user = os.environ.get('DASHBOARD_USER', 'admin')
    if not auth or auth.username != expected_user or auth.password != password:
        return Response(
            'Access denied',
            401,
            {'WWW-Authenticate': 'Basic realm="Social Media Dashboard"'},
        )


@social_dashboard_bp.route('/social', methods=['GET'])
def dashboard():
    html_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'static', 'social_dashboard.html'
    )
    with open(os.path.abspath(html_path), 'r') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@social_dashboard_bp.route('/social/accounts', methods=['GET'])
def dashboard_accounts():
    if not os.environ.get('BLOTATO_API_KEY'):
        return jsonify({"error": "BLOTATO_API_KEY is not configured"}), 500
    try:
        result = list_accounts()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Dashboard accounts: {e}")
        return jsonify({"error": str(e)}), 500


@social_dashboard_bp.route('/social/compose', methods=['POST'])
def dashboard_compose():
    if not os.environ.get('BLOTATO_API_KEY'):
        return jsonify({"error": "BLOTATO_API_KEY is not configured"}), 500
    data = request.get_json() or {}
    try:
        result = create_post(data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Dashboard compose: {e}")
        return jsonify({"error": str(e)}), 500


@social_dashboard_bp.route('/social/posts', methods=['GET'])
def dashboard_posts():
    if not os.environ.get('BLOTATO_API_KEY'):
        return jsonify({"error": "BLOTATO_API_KEY is not configured"}), 500
    try:
        result = list_posts(
            status=request.args.get('status'),
            platform=request.args.get('platform'),
            limit=int(request.args.get('limit', 50)),
            cursor=request.args.get('cursor'),
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Dashboard posts: {e}")
        return jsonify({"error": str(e)}), 500


@social_dashboard_bp.route('/social/schedules', methods=['GET'])
def dashboard_schedules():
    if not os.environ.get('BLOTATO_API_KEY'):
        return jsonify({"error": "BLOTATO_API_KEY is not configured"}), 500
    try:
        result = list_schedules(
            limit=int(request.args.get('limit', 20)),
            cursor=request.args.get('cursor'),
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Dashboard schedules: {e}")
        return jsonify({"error": str(e)}), 500


@social_dashboard_bp.route('/social/schedules/<schedule_id>', methods=['DELETE'])
def dashboard_delete_schedule(schedule_id):
    if not os.environ.get('BLOTATO_API_KEY'):
        return jsonify({"error": "BLOTATO_API_KEY is not configured"}), 500
    try:
        result = delete_schedule(schedule_id)
        return jsonify(result or {"ok": True}), 200
    except Exception as e:
        logger.error(f"Dashboard delete schedule {schedule_id}: {e}")
        return jsonify({"error": str(e)}), 500


@social_dashboard_bp.route('/social/analytics/<post_id>', methods=['GET'])
def dashboard_analytics(post_id):
    if not os.environ.get('BLOTATO_API_KEY'):
        return jsonify({"error": "BLOTATO_API_KEY is not configured"}), 500
    try:
        result = get_post_analytics(post_id)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Dashboard analytics {post_id}: {e}")
        return jsonify({"error": str(e)}), 500
