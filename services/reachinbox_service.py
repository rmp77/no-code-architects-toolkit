import requests
import logging

logger = logging.getLogger(__name__)

REACHINBOX_API = "https://api.reachinbox.ai/api/v1"


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_campaigns(api_key):
    """Returns list of campaigns: [{id, name, status}]"""
    r = requests.get(f"{REACHINBOX_API}/campaigns", headers=_headers(api_key), timeout=15)
    r.raise_for_status()
    data = r.json()
    campaigns = data.get("data", data) if isinstance(data, dict) else data
    return [
        {
            "id": str(c.get("id", "")),
            "name": c.get("name", "Unnamed"),
            "status": c.get("status", ""),
        }
        for c in (campaigns if isinstance(campaigns, list) else [])
    ]


def add_leads_to_campaign(campaign_id, leads, api_key):
    """
    Push a list of lead dicts into a ReachInbox campaign.
    Each lead needs at minimum: email, firstName, lastName.
    Returns (added_count, duplicate_count, errors[]).
    """
    payload_leads = []
    for lead in leads:
        contacts = lead.get("contacts") or []
        primary = contacts[0] if contacts else {}
        first = primary.get("first_name", "") or ""
        last = primary.get("last_name", "") or ""

        email = ""
        if contacts and contacts[0].get("email"):
            email = contacts[0]["email"]

        if not email:
            continue

        payload_leads.append({
            "email": email,
            "firstName": first,
            "lastName": last,
            "companyName": lead.get("name", ""),
            "phone": lead.get("phone", ""),
            "website": lead.get("website", ""),
        })

    if not payload_leads:
        return 0, 0, ["No leads with verified emails to push"]

    payload = {
        "campaignId": str(campaign_id),
        "leads": payload_leads,
        "newCoreVariables": ["firstName", "lastName", "companyName", "phone", "website"],
        "duplicates": [],
    }

    r = requests.post(
        f"{REACHINBOX_API}/leads/add",
        json=payload,
        headers=_headers(api_key),
        timeout=30,
    )
    r.raise_for_status()
    result = r.json()

    added = len(payload_leads)
    duplicates = len(result.get("duplicates", []))
    return added - duplicates, duplicates, []
