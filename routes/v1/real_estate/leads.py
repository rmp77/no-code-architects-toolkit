from flask import Blueprint, request, jsonify
import logging
import sqlite3
from datetime import datetime

from services.real_estate_db import _db
from services.real_estate_qualification import qualify_lead, generate_transfer_script
from services.real_estate_transfer import get_best_buyer, record_transfer, complete_transfer

logger = logging.getLogger(__name__)

re_leads_bp = Blueprint('re_leads', __name__)


def _require_api_key():
    import os
    key = os.environ.get("API_KEY")
    if key and request.headers.get("X-API-Key") != key:
        return jsonify({"error": "Unauthorized"}), 401
    return None


@re_leads_bp.route('/v1/real_estate/lead/intake', methods=['POST'])
def intake_lead():
    """
    Receive an inbound lead — manual entry or webhook from any call-tracking tool.
    Body (all optional except caller_phone):
      caller_phone, caller_name, address, source, call_sid, transcript, lead_details{}
    """
    auth = _require_api_key()
    if auth:
        return auth

    data = request.get_json(force=True, silent=True) or {}
    caller_phone = data.get("caller_phone", "").strip()
    if not caller_phone:
        return jsonify({"error": "caller_phone is required"}), 400

    transcript = data.get("transcript", "")
    lead_details = data.get("lead_details", {})
    if data.get("address"):
        lead_details.setdefault("address", data["address"])

    qualification = qualify_lead(transcript=transcript, lead_details=lead_details)

    with _db() as c:
        cur = c.execute(
            """INSERT INTO re_leads
               (caller_name, caller_phone, address, lead_type, qualification_score,
                qualification_notes, motivation_level, timeline, asking_price,
                condition, status, source, call_sid, raw_transcript)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data.get("caller_name"),
                caller_phone,
                data.get("address"),
                qualification.get("lead_type", "unknown"),
                qualification.get("score", 0),
                qualification.get("notes"),
                qualification.get("motivation_level", "cold"),
                qualification.get("timeline"),
                qualification.get("asking_price"),
                qualification.get("condition"),
                "qualified" if qualification.get("transfer_recommendation") else "new",
                data.get("source", "manual"),
                data.get("call_sid"),
                transcript or None,
            ),
        )
        lead_id = cur.lastrowid

    return jsonify({
        "lead_id": lead_id,
        "qualification": qualification,
        "next_action": "transfer" if qualification.get("transfer_recommendation") else "follow_up",
    }), 201


@re_leads_bp.route('/v1/real_estate/lead/qualify', methods=['POST'])
def qualify_existing_lead():
    """Re-qualify an existing lead with new transcript or notes."""
    auth = _require_api_key()
    if auth:
        return auth

    data = request.get_json(force=True, silent=True) or {}
    lead_id = data.get("lead_id")
    if not lead_id:
        return jsonify({"error": "lead_id is required"}), 400

    with _db() as c:
        lead = c.execute("SELECT * FROM re_leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    transcript = data.get("transcript", lead["raw_transcript"] or "")
    lead_details = {
        "address": lead["address"],
        "caller_name": lead["caller_name"],
        **data.get("lead_details", {}),
    }
    qualification = qualify_lead(transcript=transcript, lead_details=lead_details)

    with _db() as c:
        c.execute(
            """UPDATE re_leads SET
               lead_type=?, qualification_score=?, qualification_notes=?,
               motivation_level=?, timeline=?, asking_price=?, condition=?,
               status=?, raw_transcript=?
               WHERE id=?""",
            (
                qualification.get("lead_type", "unknown"),
                qualification.get("score", 0),
                qualification.get("notes"),
                qualification.get("motivation_level", "cold"),
                qualification.get("timeline"),
                qualification.get("asking_price"),
                qualification.get("condition"),
                "qualified" if qualification.get("transfer_recommendation") else "new",
                transcript or lead["raw_transcript"],
                lead_id,
            ),
        )

    return jsonify({"lead_id": lead_id, "qualification": qualification}), 200


@re_leads_bp.route('/v1/real_estate/lead/transfer', methods=['POST'])
def transfer_lead():
    """
    Execute a live transfer for a qualified lead.
    Body: lead_id, buyer_id (optional — auto-selects if omitted), method, notes
    """
    auth = _require_api_key()
    if auth:
        return auth

    data = request.get_json(force=True, silent=True) or {}
    lead_id = data.get("lead_id")
    if not lead_id:
        return jsonify({"error": "lead_id is required"}), 400

    with _db() as c:
        lead = c.execute("SELECT * FROM re_leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    lead = dict(lead)
    buyer_id = data.get("buyer_id")
    if buyer_id:
        with _db() as c:
            buyer = c.execute("SELECT * FROM re_buyers WHERE id = ?", (buyer_id,)).fetchone()
        buyer = dict(buyer) if buyer else None
    else:
        buyer = get_best_buyer(lead["lead_type"], service_area=lead.get("address"))

    if not buyer:
        return jsonify({"error": "No active buyers available for this lead type"}), 404

    fee = buyer.get("fee_amount", 0)
    transfer_id = record_transfer(
        lead_id=lead_id,
        buyer_id=buyer["id"],
        fee_amount=fee,
        method=data.get("method", "phone"),
        notes=data.get("notes", ""),
    )

    script = generate_transfer_script(lead, buyer)

    return jsonify({
        "transfer_id": transfer_id,
        "lead_id": lead_id,
        "buyer": {
            "id": buyer["id"],
            "name": buyer["name"],
            "phone": buyer["phone"],
            "type": buyer["type"],
        },
        "fee_amount": fee,
        "transfer_script": script,
        "status": "pending",
    }), 201


@re_leads_bp.route('/v1/real_estate/transfer/<int:transfer_id>/complete', methods=['POST'])
def mark_transfer_complete(transfer_id):
    auth = _require_api_key()
    if auth:
        return auth
    complete_transfer(transfer_id)
    return jsonify({"transfer_id": transfer_id, "status": "completed"}), 200


@re_leads_bp.route('/v1/real_estate/leads', methods=['GET'])
def list_leads():
    auth = _require_api_key()
    if auth:
        return auth
    status = request.args.get("status")
    lead_type = request.args.get("lead_type")
    limit = min(int(request.args.get("limit", 50)), 200)

    with _db() as c:
        query = "SELECT * FROM re_leads WHERE 1=1"
        params: list = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if lead_type:
            query += " AND lead_type = ?"
            params.append(lead_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        leads = [dict(r) for r in c.execute(query, params).fetchall()]

    return jsonify(leads), 200
