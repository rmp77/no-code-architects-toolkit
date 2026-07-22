from flask import Blueprint, request, jsonify
from services.real_estate_db import _db
from services.real_estate_transfer import (
    get_all_buyers, create_buyer, update_buyer, get_revenue_summary
)
import os

re_buyers_bp = Blueprint('re_buyers', __name__)


def _require_api_key():
    key = os.environ.get("API_KEY")
    if key and request.headers.get("X-API-Key") != key:
        return jsonify({"error": "Unauthorized"}), 401
    return None


@re_buyers_bp.route('/v1/real_estate/buyers', methods=['GET'])
def list_buyers():
    auth = _require_api_key()
    if auth:
        return auth
    buyer_type = request.args.get("type")
    active_only = request.args.get("active", "true").lower() == "true"
    return jsonify(get_all_buyers(buyer_type=buyer_type, active_only=active_only)), 200


@re_buyers_bp.route('/v1/real_estate/buyers', methods=['POST'])
def add_buyer():
    auth = _require_api_key()
    if auth:
        return auth
    data = request.get_json(force=True, silent=True) or {}
    for field in ("name", "phone", "type"):
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400
    if data["type"] not in ("wholesaler", "listing_agent"):
        return jsonify({"error": "type must be 'wholesaler' or 'listing_agent'"}), 400
    buyer = create_buyer(data)
    return jsonify(buyer), 201


@re_buyers_bp.route('/v1/real_estate/buyers/<int:buyer_id>', methods=['PATCH'])
def update_buyer_route(buyer_id):
    auth = _require_api_key()
    if auth:
        return auth
    data = request.get_json(force=True, silent=True) or {}
    if update_buyer(buyer_id, data):
        with _db() as c:
            buyer = c.execute("SELECT * FROM re_buyers WHERE id=?", (buyer_id,)).fetchone()
        return jsonify(dict(buyer)), 200
    return jsonify({"error": "No valid fields to update"}), 400


@re_buyers_bp.route('/v1/real_estate/buyers/<int:buyer_id>', methods=['DELETE'])
def deactivate_buyer(buyer_id):
    auth = _require_api_key()
    if auth:
        return auth
    update_buyer(buyer_id, {"active": 0})
    return jsonify({"buyer_id": buyer_id, "active": False}), 200


@re_buyers_bp.route('/v1/real_estate/revenue', methods=['GET'])
def revenue_summary():
    auth = _require_api_key()
    if auth:
        return auth
    return jsonify(get_revenue_summary()), 200


@re_buyers_bp.route('/v1/real_estate/transfers', methods=['GET'])
def list_transfers():
    auth = _require_api_key()
    if auth:
        return auth
    limit = min(int(request.args.get("limit", 50)), 200)
    with _db() as c:
        rows = c.execute(
            """SELECT t.*, l.caller_name, l.caller_phone, l.address, l.lead_type,
                      b.name as buyer_name, b.type as buyer_type
               FROM re_transfers t
               JOIN re_leads l ON t.lead_id = l.id
               JOIN re_buyers b ON t.buyer_id = b.id
               ORDER BY t.transferred_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return jsonify([dict(r) for r in rows]), 200
