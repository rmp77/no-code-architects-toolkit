import os
import logging
import requests
import json

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("RE_AI_MODEL", "openai/gpt-4o-mini")

# Greenlight formula: unique headline + featured image keyword + keyword body + CTA to YOUR number
AD_TYPES = {
    "motivated_seller": {
        "label": "Motivated Seller",
        "category": "real estate for sale",
        "description": "Attract sellers who need to sell fast",
    },
    "buyer": {
        "label": "Buyer / Investor",
        "category": "real estate wanted",
        "description": "Attract cash buyers and investors",
    },
    "investor": {
        "label": "Investor Opportunity",
        "category": "real estate for sale",
        "description": "Off-market investment properties",
    },
}

GREENLIGHT_SYSTEM_PROMPT = """You generate Craigslist real estate ads using the Greenlight formula for Deal Flow Direct in San Diego, CA.

Greenlight formula rules:
1. UNIQUE HEADLINE: Specific, curiosity-driven, NOT generic ("3/2 house for sale" = bad). Include a specific detail, number, or hook.
2. UNIQUE FEATURED IMAGE: Describe what the image should show (you can't upload but describe it for the user)
3. KEYWORD-PACKED BODY: Naturally weave in search terms buyers/sellers use. Paragraphs, not bullet lists.
4. STRONG CTA: End with a call to the tracking phone number. Create urgency.
5. Keep it human, not corporate. Conversational tone. San Diego specific.
6. For motivated seller ads: speak TO sellers, create trust, promise fast/easy process.
7. For buyer/investor ads: speak TO buyers, highlight deal quality, create FOMO.

Return ONLY valid JSON:
{
  "headline": "...",
  "image_description": "...",
  "body": "full ad body text with paragraphs",
  "cta": "call to action text",
  "keywords": ["keyword1", "keyword2", ...],
  "renewal_tip": "what to change on renewal to stay unique"
}"""


def generate_craigslist_ad(ad_type: str, tracking_phone: str,
                            location: str = "San Diego, CA",
                            custom_notes: str = "") -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return _fallback_ad(ad_type, tracking_phone, location)

    type_info = AD_TYPES.get(ad_type, AD_TYPES["motivated_seller"])
    user_msg = (
        f"Create a {type_info['label']} Craigslist ad for {location}. "
        f"Tracking phone number: {tracking_phone}. "
        f"Ad category: {type_info['category']}. "
        f"{f'Additional notes: {custom_notes}' if custom_notes else ''}"
    )

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": GREENLIGHT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.8,
                "max_tokens": 800,
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Ad generation error: {e}")
        return _fallback_ad(ad_type, tracking_phone, location)


def _fallback_ad(ad_type: str, tracking_phone: str, location: str) -> dict:
    if ad_type == "motivated_seller":
        return {
            "headline": f"We Buy Houses {location} — Any Condition, Close in 7 Days",
            "image_description": "Photo of a house with a 'We Buy Houses' sign in front yard",
            "body": (
                f"Facing foreclosure, divorce, or just need to sell fast? "
                f"We buy houses in {location} in any condition — no repairs, no commissions, no hassle. "
                f"Whether it's inherited, vacant, or needs major work, we'll make you a fair cash offer. "
                f"We close on YOUR timeline, sometimes in as little as 7 days. "
                f"No fees. No realtor commissions. Just a fast, stress-free sale."
            ),
            "cta": f"Call or text now for your free cash offer: {tracking_phone}",
            "keywords": ["we buy houses", "cash offer", "sell fast", "any condition", "foreclosure", "probate"],
            "renewal_tip": "Change the headline number or lead with a different pain point (divorce, inherited, etc.)",
        }
    return {
        "headline": f"Off-Market Investment Properties in {location} — Cash Buyers Only",
        "image_description": "Aerial photo of a San Diego neighborhood with investment potential",
        "body": (
            f"Are you a cash buyer or real estate investor looking for off-market deals in {location}? "
            f"We connect serious buyers with motivated sellers before properties hit the MLS. "
            f"Get first access to distressed properties, foreclosures, and estate sales. "
            f"No bidding wars. No wasted time on the open market."
        ),
        "cta": f"Text your buying criteria to {tracking_phone} and we'll match you with deals.",
        "keywords": ["off market", "cash buyer", "investment property", "wholesale", "distressed", "San Diego investor"],
        "renewal_tip": "Lead with a specific deal type (probate, estate sale, foreclosure) to stay fresh.",
    }


def get_renewal_checklist(ad: dict) -> list[str]:
    """Return a 48-hour renewal checklist for a Craigslist ad."""
    return [
        f"Change headline: currently '{ad.get('headline', '')[:50]}...' — pick a different hook",
        "Swap featured image (different photo or angle)",
        "Rotate opening paragraph — lead with a different pain point or benefit",
        "Update CTA — add urgency (e.g. 'Spots limited this week')",
        "Vary at least 2-3 keyword phrases to avoid Craigslist duplicate detection",
        "Check and repost in correct category before 48-hour expiry",
    ]
