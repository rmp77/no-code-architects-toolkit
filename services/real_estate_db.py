import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deal_flow_direct.db')


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with _db() as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS re_buyers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                company         TEXT,
                email           TEXT,
                phone           TEXT NOT NULL,
                type            TEXT NOT NULL CHECK(type IN ('wholesaler','listing_agent')),
                fee_amount      REAL NOT NULL DEFAULT 0,
                fee_type        TEXT NOT NULL DEFAULT 'per_transfer' CHECK(fee_type IN ('per_transfer','monthly')),
                buy_criteria    TEXT,
                service_areas   TEXT,
                active          INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS re_leads (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_name         TEXT,
                caller_phone        TEXT NOT NULL,
                address             TEXT,
                lead_type           TEXT CHECK(lead_type IN ('buyer','motivated_seller','unknown')),
                qualification_score INTEGER DEFAULT 0,
                qualification_notes TEXT,
                motivation_level    TEXT CHECK(motivation_level IN ('hot','warm','cold','unqualified')),
                timeline            TEXT,
                asking_price        REAL,
                arv_estimate        REAL,
                condition           TEXT,
                status              TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','qualified','transferred','rejected','no_answer')),
                source              TEXT DEFAULT 'craigslist',
                call_sid            TEXT,
                craigslist_ad_id    INTEGER REFERENCES re_craigslist_ads(id),
                raw_transcript      TEXT,
                created_at          TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS re_transfers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id         INTEGER NOT NULL REFERENCES re_leads(id),
                buyer_id        INTEGER NOT NULL REFERENCES re_buyers(id),
                fee_amount      REAL NOT NULL DEFAULT 0,
                status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','completed','failed','refunded')),
                transfer_method TEXT DEFAULT 'phone' CHECK(transfer_method IN ('phone','email','sms')),
                notes           TEXT,
                transferred_at  TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at    TEXT
            );

            CREATE TABLE IF NOT EXISTS re_craigslist_ads (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                headline        TEXT NOT NULL,
                body            TEXT NOT NULL,
                image_url       TEXT,
                tracking_phone  TEXT NOT NULL,
                category        TEXT DEFAULT 'real_estate',
                ad_type         TEXT DEFAULT 'motivated_seller' CHECK(ad_type IN ('motivated_seller','buyer','investor')),
                posted_at       TEXT,
                expires_at      TEXT,
                renewal_count   INTEGER NOT NULL DEFAULT 0,
                status          TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','expired','paused')),
                leads_count     INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS re_youtube_videos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                zillow_url      TEXT,
                property_address TEXT,
                youtube_video_id TEXT,
                youtube_url     TEXT,
                title           TEXT,
                tracking_phone  TEXT,
                status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','processing','published','failed')),
                views           INTEGER DEFAULT 0,
                leads_generated INTEGER DEFAULT 0,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );
        ''')


try:
    init_db()
except Exception as e:
    logger.error(f"DB init error: {e}")
