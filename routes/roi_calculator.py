from flask import Blueprint, send_file, request, jsonify
import os
import sqlite3
import json
import threading
import logging
from datetime import datetime

from services.monday_service import get_or_create_funnel_board, push_funnel_lead

logger = logging.getLogger(__name__)

roi_calculator_bp = Blueprint('roi_calculator', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'roi_leads.db')


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS roi_submissions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT,
            email        TEXT,
            phone        TEXT,
            path         TEXT,
            cpc          INTEGER,
            biz_type     TEXT,
            utm_source   TEXT,
            data_json    TEXT,
            submitted_at TEXT
        )''')


try:
    _init_db()
except Exception:
    pass


def _push_to_monday(lead):
    """Background thread: push a funnel lead to Monday.com Funnel Leads board."""
    token        = os.environ.get('MONDAY_API_TOKEN')
    workspace_id = os.environ.get('MONDAY_WORKSPACE_ID')
    if not token or not workspace_id:
        return
    try:
        board_id, col_ids = get_or_create_funnel_board(workspace_id, token)
        item_id, status   = push_funnel_lead(board_id, col_ids, lead, token)
        logger.info(f"Monday funnel lead {status}: {lead.get('email')} → item {item_id}")
    except Exception as e:
        logger.error(f"Monday funnel push failed for {lead.get('email')}: {e}")


@roi_calculator_bp.route('/roi')
def roi_calculator():
    html_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'roi_calculator.html'
    )
    return send_file(os.path.abspath(html_path))


@roi_calculator_bp.route('/roi/submit', methods=['POST'])
def roi_submit():
    data       = request.get_json(silent=True) or {}
    name       = str(data.get('name',     '')).strip()[:100]
    email      = str(data.get('email',    '')).strip()[:200]
    phone      = str(data.get('phone',    '')).strip()[:30]
    path       = str(data.get('path',     '')).strip()[:20]
    biz_type   = str(data.get('biz_type', '')).strip()[:100]
    cpc        = int(data.get('cpc',       0))
    utm        = data.get('utm', {}) or {}
    utm_source = str(utm.get('utm_source', '')).strip()[:100]

    # Save to local DB
    try:
        with _db() as c:
            c.execute(
                'INSERT INTO roi_submissions '
                '(name, email, phone, path, cpc, biz_type, utm_source, data_json, submitted_at) '
                'VALUES (?,?,?,?,?,?,?,?,?)',
                (name, email, phone, path, cpc, biz_type, utm_source,
                 json.dumps(data), datetime.utcnow().isoformat())
            )
    except Exception as e:
        logger.error(f"DB insert failed: {e}")

    # Push to Monday.com in background — never blocks the prospect's UX
    if email:
        lead = {
            'name':       name,
            'email':      email,
            'phone':      phone,
            'path':       path,
            'cpc':        cpc,
            'biz_type':   biz_type,
            'utm_source': utm_source,
        }
        threading.Thread(target=_push_to_monday, args=(lead,), daemon=True).start()

    return jsonify({'ok': True})


@roi_calculator_bp.route('/roi/leads')
def roi_leads():
    try:
        with _db() as c:
            rows = c.execute(
                'SELECT id, name, email, phone, path, cpc, biz_type, utm_source, submitted_at '
                'FROM roi_submissions ORDER BY submitted_at DESC LIMIT 200'
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        return jsonify([])
