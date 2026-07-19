from flask import Blueprint, request, jsonify
from services.leads_service import run_leads_search
from services.monday_service import get_or_create_board, push_lead
from services.reachinbox_service import get_campaigns, add_leads_to_campaign
import logging
import os

leads_dashboard_bp = Blueprint('leads_dashboard', __name__)
logger = logging.getLogger(__name__)


@leads_dashboard_bp.route('/leads', methods=['GET'])
def dashboard():
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'leads_dashboard.html')
    with open(os.path.abspath(html_path), 'r') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@leads_dashboard_bp.route('/leads/search', methods=['POST'])
def dashboard_search():
    data = request.get_json() or {}
    business_type = data.get('business_type', '').strip()
    location = data.get('location', '').strip()
    limit = min(int(data.get('limit', 10)), 20)

    if not business_type or not location:
        return jsonify({"error": "business_type and location are required"}), 400

    maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    prospeo_key = os.environ.get('PROSPEO_API_KEY')
    owinja_key = os.environ.get('OPENWEBNINJA_KEY')
    blitz_key = os.environ.get('BLITZ_API_KEY')
    mv_key = os.environ.get('MILLIONVERIFIER_API_KEY')

    if not maps_key:
        return jsonify({"error": "GOOGLE_MAPS_API_KEY is not configured"}), 500

    try:
        result = run_leads_search(business_type, location, limit, maps_key, prospeo_key, owinja_key, blitz_key, mv_key)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Dashboard search failed: {e}")
        return jsonify({"error": str(e)}), 500


@leads_dashboard_bp.route('/leads/monday', methods=['POST'])
def monday_export():
    data = request.get_json() or {}
    leads = data.get('leads', [])
    if not leads:
        return jsonify({"error": "No leads provided"}), 400

    token = os.environ.get('MONDAY_API_TOKEN')
    workspace_id = os.environ.get('MONDAY_WORKSPACE_ID')
    if not token or not workspace_id:
        return jsonify({"error": "MONDAY_API_TOKEN or MONDAY_WORKSPACE_ID is not configured"}), 500

    try:
        board_id, col_ids = get_or_create_board(workspace_id, token)
        results = []
        for lead in leads:
            try:
                item_id, status = push_lead(board_id, col_ids, lead, token)
                results.append({"name": lead.get("name"), "status": status, "item_id": item_id, "ok": True})
            except Exception as e:
                logger.warning(f"Failed to push lead '{lead.get('name')}': {e}")
                results.append({"name": lead.get("name"), "status": "error", "ok": False, "error": str(e)})

        pushed     = sum(1 for r in results if r.get("status") == "created")
        duplicates = sum(1 for r in results if r.get("status") == "duplicate")
        return jsonify({
            "pushed": pushed,
            "duplicates": duplicates,
            "total": len(leads),
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"Monday.com export failed: {e}")
        return jsonify({"error": str(e)}), 500


@leads_dashboard_bp.route('/leads/reachinbox/campaigns', methods=['GET'])
def reachinbox_campaigns():
    api_key = os.environ.get('REACHINBOX_API_KEY')
    if not api_key:
        return jsonify({"error": "REACHINBOX_API_KEY is not configured"}), 500
    try:
        campaigns = get_campaigns(api_key)
        return jsonify({"campaigns": campaigns}), 200
    except Exception as e:
        logger.error(f"ReachInbox campaign fetch failed: {e}")
        return jsonify({"error": str(e)}), 500


@leads_dashboard_bp.route('/leads/reachinbox', methods=['POST'])
def reachinbox_export():
    data = request.get_json() or {}
    leads = data.get('leads', [])
    campaign_id = data.get('campaign_id', '')

    if not leads:
        return jsonify({"error": "No leads provided"}), 400
    if not campaign_id:
        return jsonify({"error": "campaign_id is required"}), 400

    api_key = os.environ.get('REACHINBOX_API_KEY')
    if not api_key:
        return jsonify({"error": "REACHINBOX_API_KEY is not configured"}), 500

    try:
        added, duplicates, errors = add_leads_to_campaign(campaign_id, leads, api_key)
        return jsonify({
            "pushed": added,
            "duplicates": duplicates,
            "total": len(leads),
            "errors": errors,
        }), 200
    except Exception as e:
        logger.error(f"ReachInbox export failed: {e}")
        return jsonify({"error": str(e)}), 500
