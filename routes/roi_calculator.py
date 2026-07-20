from flask import Blueprint, send_file, request, jsonify
import os
import sqlite3
import json
from datetime import datetime

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
            utm_source   TEXT,
            data_json    TEXT,
            submitted_at TEXT
        )''')


try:
    _init_db()
except Exception:
    pass


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
    name       = str(data.get('name',  '')).strip()[:100]
    email      = str(data.get('email', '')).strip()[:200]
    phone      = str(data.get('phone', '')).strip()[:30]
    path       = str(data.get('path',  '')).strip()[:20]
    cpc        = int(data.get('cpc',   0))
    utm        = data.get('utm', {}) or {}
    utm_source = str(utm.get('utm_source', '')).strip()[:100]
    try:
        with _db() as c:
            c.execute(
                'INSERT INTO roi_submissions '
                '(name, email, phone, path, cpc, utm_source, data_json, submitted_at) '
                'VALUES (?,?,?,?,?,?,?,?)',
                (name, email, phone, path, cpc, utm_source, json.dumps(data), datetime.utcnow().isoformat())
            )
    except Exception:
        pass
    return jsonify({'ok': True})


@roi_calculator_bp.route('/roi/leads')
def roi_leads():
    try:
        with _db() as c:
            rows = c.execute(
                'SELECT id, name, email, phone, path, cpc, utm_source, submitted_at '
                'FROM roi_submissions ORDER BY submitted_at DESC LIMIT 200'
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        return jsonify([])
