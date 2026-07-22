import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("RE_AI_MODEL", "openai/gpt-4o-mini")

QUALIFICATION_PROMPT = """You are an AI qualifier for a real estate lead transfer business called Deal Flow Direct in San Diego, CA.

A caller has contacted us about a property. Analyze the conversation transcript or lead details and determine:
1. Lead type: "motivated_seller" (they want to sell), "buyer" (they want to buy/invest), or "unknown"
2. Motivation level: "hot" (must sell within 30 days), "warm" (3-6 months), "cold" (no urgency), or "unqualified" (not a real lead)
3. Qualification score: 0-100 (100 = perfect live transfer candidate)
4. Key qualification notes: brief bullet points
5. Estimated timeline
6. Asking price if mentioned (null if not)
7. Property condition if mentioned

For motivated sellers, score high if: distressed situation (divorce, foreclosure, probate, job loss), flexible on price, can close fast, property needs work.
For buyers/investors, score high if: has cash or proof of funds, buying criteria is clear, active market participant.

Respond with ONLY valid JSON matching this schema:
{
  "lead_type": "motivated_seller" | "buyer" | "unknown",
  "motivation_level": "hot" | "warm" | "cold" | "unqualified",
  "score": 0-100,
  "notes": "bullet point notes",
  "timeline": "string or null",
  "asking_price": number_or_null,
  "condition": "string or null",
  "transfer_recommendation": true | false,
  "transfer_to": "wholesaler" | "listing_agent" | null
}"""


def qualify_lead(transcript: str = "", lead_details: dict = None) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return _default_qualification()

    content = transcript or ""
    if lead_details:
        content += f"\n\nLead details: {json.dumps(lead_details)}"

    if not content.strip():
        return _default_qualification()

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": QUALIFICATION_PROMPT},
                    {"role": "user", "content": content},
                ],
                "temperature": 0.2,
                "max_tokens": 500,
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Qualification AI error: {e}")
        return _default_qualification()


def _default_qualification() -> dict:
    return {
        "lead_type": "unknown",
        "motivation_level": "cold",
        "score": 0,
        "notes": "Manual review required — AI qualification unavailable.",
        "timeline": None,
        "asking_price": None,
        "condition": None,
        "transfer_recommendation": False,
        "transfer_to": None,
    }


def generate_transfer_script(lead: dict, buyer: dict) -> str:
    """Generate a live-transfer intro script for the agent making the call."""
    return (
        f"Hi {buyer.get('name', 'there')}, this is Deal Flow Direct. "
        f"I have a {'motivated seller' if lead.get('lead_type') == 'motivated_seller' else 'buyer lead'} "
        f"on the line for you. "
        f"Property: {lead.get('address', 'San Diego area')}. "
        f"Score: {lead.get('qualification_score', 'N/A')}/100. "
        f"Notes: {lead.get('qualification_notes', '')}. "
        f"Connecting now — please stand by."
    )
