from flask import Blueprint, request, jsonify
from services.leads_service import run_leads_search
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

    if not maps_key:
        return jsonify({"error": "GOOGLE_MAPS_API_KEY is not configured"}), 500

    try:
        result = run_leads_search(business_type, location, limit, maps_key, prospeo_key)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Dashboard search failed: {e}")
        return jsonify({"error": str(e)}), 500
