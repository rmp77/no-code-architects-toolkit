from flask import Blueprint, send_file, request, jsonify, Response
import os
import sqlite3
from functools import wraps
from services.real_estate_db import _db
from services.real_estate_transfer import get_revenue_summary, get_all_buyers

dfd_bp = Blueprint('deal_flow_direct', __name__)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')


def _auth_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        password = os.environ.get("DASHBOARD_PASSWORD")
        if not password:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or auth.password != password:
            return Response(
                "Authentication required",
                401,
                {"WWW-Authenticate": 'Basic realm="Deal Flow Direct"'},
            )
        return f(*args, **kwargs)
    return wrapped


@dfd_bp.route('/dfd')
@_auth_required
def dashboard():
    return send_file(os.path.join(STATIC_DIR, 'deal_flow_direct.html'))


@dfd_bp.route('/dfd/data')
@_auth_required
def dashboard_data():
    summary = get_revenue_summary()
    buyers = get_all_buyers()

    with _db() as c:
        recent_leads = [dict(r) for r in c.execute(
            "SELECT * FROM re_leads ORDER BY created_at DESC LIMIT 20"
        ).fetchall()]
        recent_transfers = [dict(r) for r in c.execute(
            """SELECT t.*, l.caller_name, l.caller_phone, l.address, l.lead_type,
                      b.name as buyer_name
               FROM re_transfers t
               JOIN re_leads l ON t.lead_id = l.id
               JOIN re_buyers b ON t.buyer_id = b.id
               ORDER BY t.transferred_at DESC LIMIT 20""",
        ).fetchall()]
        active_ads = [dict(r) for r in c.execute(
            "SELECT * FROM re_craigslist_ads WHERE status='active' ORDER BY posted_at DESC"
        ).fetchall()]
        youtube_videos = [dict(r) for r in c.execute(
            "SELECT * FROM re_youtube_videos ORDER BY created_at DESC LIMIT 10"
        ).fetchall()]

        # Revenue by week (last 8 weeks)
        weekly = [dict(r) for r in c.execute("""
            SELECT strftime('%Y-W%W', transferred_at) as week,
                   SUM(fee_amount) as revenue,
                   COUNT(*) as transfers
            FROM re_transfers
            WHERE status='completed'
            GROUP BY week
            ORDER BY week DESC
            LIMIT 8
        """).fetchall()]

    return jsonify({
        "summary": summary,
        "buyers": buyers,
        "recent_leads": recent_leads,
        "recent_transfers": recent_transfers,
        "active_ads": active_ads,
        "youtube_videos": youtube_videos,
        "weekly_revenue": list(reversed(weekly)),
        "tracking_phone": os.environ.get("RE_TRACKING_PHONE", "Not configured"),
    }), 200
