from flask import Blueprint, request, jsonify
from services.real_estate_db import _db
from services.real_estate_craigslist import generate_craigslist_ad, get_renewal_checklist
from services.real_estate_youtube import scrape_zillow_property, generate_video_script, get_invideo_automation_config
import os
from datetime import datetime, timedelta

re_ads_bp = Blueprint('re_ads', __name__)


def _require_api_key():
    key = os.environ.get("API_KEY")
    if key and request.headers.get("X-API-Key") != key:
        return jsonify({"error": "Unauthorized"}), 401
    return None


# ── Craigslist Ad Routes ──────────────────────────────────────────────────────

@re_ads_bp.route('/v1/real_estate/craigslist/generate', methods=['POST'])
def generate_ad():
    auth = _require_api_key()
    if auth:
        return auth
    data = request.get_json(force=True, silent=True) or {}
    tracking_phone = data.get("tracking_phone", os.environ.get("RE_TRACKING_PHONE", ""))
    if not tracking_phone:
        return jsonify({"error": "tracking_phone is required (or set RE_TRACKING_PHONE env var)"}), 400

    ad_content = generate_craigslist_ad(
        ad_type=data.get("ad_type", "motivated_seller"),
        tracking_phone=tracking_phone,
        location=data.get("location", "San Diego, CA"),
        custom_notes=data.get("custom_notes", ""),
    )

    with _db() as c:
        cur = c.execute(
            """INSERT INTO re_craigslist_ads
               (headline, body, tracking_phone, ad_type, status)
               VALUES (?,?,?,?,?)""",
            (
                ad_content.get("headline", ""),
                f"{ad_content.get('body', '')}\n\n{ad_content.get('cta', '')}",
                tracking_phone,
                data.get("ad_type", "motivated_seller"),
                "draft",
            ),
        )
        ad_id = cur.lastrowid

    return jsonify({"ad_id": ad_id, **ad_content}), 201


@re_ads_bp.route('/v1/real_estate/craigslist/ads', methods=['GET'])
def list_ads():
    auth = _require_api_key()
    if auth:
        return auth
    with _db() as c:
        ads = [dict(r) for r in c.execute(
            "SELECT * FROM re_craigslist_ads ORDER BY created_at DESC LIMIT 50"
        ).fetchall()]
    return jsonify(ads), 200


@re_ads_bp.route('/v1/real_estate/craigslist/ads/<int:ad_id>/activate', methods=['POST'])
def activate_ad(ad_id):
    auth = _require_api_key()
    if auth:
        return auth
    now = datetime.utcnow()
    expires = now + timedelta(hours=48)
    with _db() as c:
        c.execute(
            "UPDATE re_craigslist_ads SET status='active', posted_at=?, expires_at=? WHERE id=?",
            (now.isoformat(), expires.isoformat(), ad_id),
        )
        ad = c.execute("SELECT * FROM re_craigslist_ads WHERE id=?", (ad_id,)).fetchone()
    if not ad:
        return jsonify({"error": "Ad not found"}), 404
    checklist = get_renewal_checklist(dict(ad))
    return jsonify({
        "ad_id": ad_id,
        "status": "active",
        "expires_at": expires.isoformat(),
        "renewal_checklist": checklist,
    }), 200


@re_ads_bp.route('/v1/real_estate/craigslist/ads/<int:ad_id>/renew', methods=['POST'])
def renew_ad(ad_id):
    auth = _require_api_key()
    if auth:
        return auth
    now = datetime.utcnow()
    expires = now + timedelta(hours=48)
    with _db() as c:
        c.execute(
            """UPDATE re_craigslist_ads
               SET renewal_count = renewal_count + 1, posted_at=?, expires_at=?, status='active'
               WHERE id=?""",
            (now.isoformat(), expires.isoformat(), ad_id),
        )
        ad = c.execute("SELECT * FROM re_craigslist_ads WHERE id=?", (ad_id,)).fetchone()
    if not ad:
        return jsonify({"error": "Ad not found"}), 404
    checklist = get_renewal_checklist(dict(ad))
    return jsonify({
        "ad_id": ad_id,
        "renewal_count": ad["renewal_count"],
        "expires_at": expires.isoformat(),
        "renewal_checklist": checklist,
    }), 200


@re_ads_bp.route('/v1/real_estate/craigslist/ads/<int:ad_id>/lead', methods=['POST'])
def record_ad_lead(ad_id):
    """Increment lead count for an ad (call after each inbound lead from that ad)."""
    auth = _require_api_key()
    if auth:
        return auth
    with _db() as c:
        c.execute(
            "UPDATE re_craigslist_ads SET leads_count = leads_count + 1 WHERE id=?", (ad_id,)
        )
    return jsonify({"ad_id": ad_id, "recorded": True}), 200


# ── YouTube Routes ────────────────────────────────────────────────────────────

@re_ads_bp.route('/v1/real_estate/youtube/prepare', methods=['POST'])
def prepare_youtube_video():
    """
    Given a Zillow URL, scrape property data and generate a video script + InVideo config.
    """
    auth = _require_api_key()
    if auth:
        return auth
    data = request.get_json(force=True, silent=True) or {}
    zillow_url = data.get("zillow_url", "").strip()
    if not zillow_url:
        return jsonify({"error": "zillow_url is required"}), 400

    tracking_phone = data.get("tracking_phone", os.environ.get("RE_TRACKING_PHONE", ""))
    if not tracking_phone:
        return jsonify({"error": "tracking_phone is required (or set RE_TRACKING_PHONE env var)"}), 400

    property_data = scrape_zillow_property(zillow_url)
    script = generate_video_script(property_data, tracking_phone)
    automation_config = get_invideo_automation_config(property_data, script, tracking_phone)

    with _db() as c:
        cur = c.execute(
            """INSERT INTO re_youtube_videos
               (zillow_url, property_address, title, tracking_phone, status)
               VALUES (?,?,?,?,'pending')""",
            (zillow_url, property_data.get("address"), script.get("title"), tracking_phone),
        )
        video_id = cur.lastrowid

    return jsonify({
        "video_id": video_id,
        "property": property_data,
        "script": script,
        "automation": automation_config,
    }), 201


@re_ads_bp.route('/v1/real_estate/youtube/complete', methods=['POST'])
def complete_youtube_video():
    """Mark a video as published after YouTube upload completes."""
    auth = _require_api_key()
    if auth:
        return auth
    data = request.get_json(force=True, silent=True) or {}
    video_id = data.get("video_id")
    youtube_video_id = data.get("youtube_video_id", "").strip()
    if not video_id or not youtube_video_id:
        return jsonify({"error": "video_id and youtube_video_id are required"}), 400

    youtube_url = f"https://www.youtube.com/watch?v={youtube_video_id}"
    with _db() as c:
        c.execute(
            "UPDATE re_youtube_videos SET youtube_video_id=?, youtube_url=?, status='published' WHERE id=?",
            (youtube_video_id, youtube_url, video_id),
        )
    return jsonify({"video_id": video_id, "youtube_url": youtube_url, "status": "published"}), 200


@re_ads_bp.route('/v1/real_estate/youtube/videos', methods=['GET'])
def list_youtube_videos():
    auth = _require_api_key()
    if auth:
        return auth
    with _db() as c:
        videos = [dict(r) for r in c.execute(
            "SELECT * FROM re_youtube_videos ORDER BY created_at DESC LIMIT 50"
        ).fetchall()]
    return jsonify(videos), 200
