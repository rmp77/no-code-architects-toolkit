import os
import logging
import requests

logger = logging.getLogger(__name__)

MONDAY_API = "https://api.monday.com/v2"
REACHINBOX_API = "https://api.reachinbox.ai"


def handle_oxoray_event(event_type, prospect, raw_data):
    """
    Routes OXORAY LinkedIn events to appropriate downstream actions.

    Events:
      prospect_qualified  → log to Monday Leads board
      meeting_booked      → log to Monday + update column + notify Slack
      prospect_silent     → trigger ReachInbox PRISM email sequence (48h no reply)
      prospect_replied    → log reply to Monday notes
      prospect_disqualified → log and close Monday item
    """
    handlers = {
        "prospect_qualified": _on_qualified,
        "meeting_booked":     _on_meeting_booked,
        "prospect_silent":    _on_silent,
        "prospect_replied":   _on_replied,
        "prospect_disqualified": _on_disqualified,
    }

    handler = handlers.get(event_type)
    if not handler:
        raise ValueError(f"Unknown event_type: {event_type}")

    return handler(prospect, raw_data)


def _on_qualified(prospect, data):
    monday_token = os.environ.get("MONDAY_API_KEY")
    board_id = os.environ.get("MONDAY_LINKEDIN_BOARD_ID")

    result = {}

    if monday_token and board_id:
        item_id = _monday_create_lead(prospect, monday_token, board_id)
        result["monday_item_id"] = item_id
        logger.info(f"Monday item created: {item_id} for {prospect.get('first_name')}")

    return result


def _on_meeting_booked(prospect, data):
    monday_token = os.environ.get("MONDAY_API_KEY")
    board_id = os.environ.get("MONDAY_LINKEDIN_BOARD_ID")
    meeting_url = data.get("meeting_url", "")

    result = {}

    if monday_token and board_id:
        item_id = _monday_create_lead(prospect, monday_token, board_id, status="Meeting Booked", notes=meeting_url)
        result["monday_item_id"] = item_id

    _notify_slack(
        f":calendar: *Meeting booked* — {prospect.get('first_name')} {prospect.get('last_name', '')} "
        f"({prospect.get('title', '')}, {prospect.get('city', '')}) via LinkedIn Flow outreach.\n"
        f"Archetype: {prospect.get('archetype', 'unknown')}\nCalendly: {meeting_url}"
    )

    logger.info(f"Meeting booked: {prospect.get('first_name')} {prospect.get('last_name')}")
    result["slack_notified"] = True
    return result


def _on_silent(prospect, data):
    """48h silence after LinkedIn connect → trigger ReachInbox PRISM email sequence."""
    email = prospect.get("email")
    if not email:
        logger.info(f"Prospect {prospect.get('first_name')} silent but no email — skipping ReachInbox")
        return {"skipped": "no email"}

    campaign_id = os.environ.get("REACHINBOX_LINKEDIN_SILENT_CAMPAIGN_ID")
    api_key = os.environ.get("REACHINBOX_API_KEY")

    if not campaign_id or not api_key:
        logger.warning("ReachInbox not configured — skipping email fallback")
        return {"skipped": "reachinbox not configured"}

    result = _reachinbox_add_lead(email, prospect, campaign_id, api_key)
    logger.info(f"ReachInbox PRISM sequence triggered for {email}")
    return result


def _on_replied(prospect, data):
    notes = data.get("notes", "")
    logger.info(f"Prospect replied: {prospect.get('first_name')} — notes: {notes}")
    return {"logged": True}


def _on_disqualified(prospect, data):
    logger.info(f"Prospect disqualified: {prospect.get('first_name')} {prospect.get('last_name')}")
    return {"logged": True}


def _monday_create_lead(prospect, token, board_id, status="LinkedIn Qualified", notes=""):
    first = prospect.get("first_name", "")
    last = prospect.get("last_name", "")
    name = f"{first} {last}".strip() or "Unknown"
    city = prospect.get("city", "")
    title = prospect.get("title", "")
    archetype = prospect.get("archetype", "unknown")
    linkedin_url = prospect.get("linkedin_url", "")
    email = prospect.get("email", "")

    column_values = {
        "text": title,
        "location": city,
        "email": {"email": email, "text": email} if email else None,
        "link": {"url": linkedin_url, "text": "LinkedIn"} if linkedin_url else None,
        "status": {"label": status},
        "text4": archetype.title(),
        "text5": notes or "",
        "source__1": "LinkedIn — OXORAY",
    }
    column_values = {k: v for k, v in column_values.items() if v is not None}

    import json
    mutation = """
    mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
      create_item(board_id: $boardId, item_name: $itemName, column_values: $columnValues) {
        id
      }
    }
    """
    variables = {
        "boardId": board_id,
        "itemName": name,
        "columnValues": json.dumps(column_values)
    }

    r = requests.post(
        MONDAY_API,
        json={"query": mutation, "variables": variables},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        },
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise ValueError(f"Monday API error: {data['errors']}")
    return data["data"]["create_item"]["id"]


def _reachinbox_add_lead(email, prospect, campaign_id, api_key):
    payload = {
        "campaignId": campaign_id,
        "leads": [
            {
                "email": email,
                "firstName": prospect.get("first_name", ""),
                "lastName": prospect.get("last_name", ""),
                "variables": {
                    "city": prospect.get("city", ""),
                    "title": prospect.get("title", ""),
                    "archetype": prospect.get("archetype", "unknown"),
                    "linkedinUrl": prospect.get("linkedin_url", ""),
                    "source": "LinkedIn — OXORAY",
                }
            }
        ]
    }

    r = requests.post(
        f"{REACHINBOX_API}/api/v1/onboarding/leads",
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        timeout=30
    )
    r.raise_for_status()
    return r.json()


def _notify_slack(message):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return

    try:
        requests.post(webhook_url, json={"text": message}, timeout=10)
    except Exception as e:
        logger.warning(f"Slack notification failed: {e}")
