import json
import requests
import logging

logger = logging.getLogger(__name__)

MONDAY_API    = "https://api.monday.com/v2"
BOARD_NAME    = "Leads"
FUNNEL_BOARD  = "Funnel Leads"

FUNNEL_COLUMN_DEFS = [
    ("Email",          "email"),
    ("Phone",          "phone"),
    ("Business Type",  "text"),
    ("Path",           "text"),
    ("Cost Per Call",  "numbers"),
    ("UTM Source",     "text"),
    ("Source",         "text"),
]

COLUMN_DEFS = [
    ("Phone",          "phone"),
    ("Website",        "link"),
    ("Address",        "text"),
    ("Rating",         "numbers"),
    ("Business Status","text"),
    ("Contact Name",   "text"),
    ("Contact Title",  "text"),
    ("Email",          "email"),
    ("Email Verified", "text"),
    ("Source",         "text"),
    ("Place ID",       "text"),  # unique key used to detect duplicates
]


def _gql(query, variables, token):
    r = requests.post(
        MONDAY_API,
        json={"query": query, "variables": variables},
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
        raise ValueError(f"Monday.com API error: {data['errors']}")
    return data.get("data", {})


def _find_board(workspace_id, token):
    q = """
    query($workspace_ids: [ID]) {
      boards(workspace_ids: $workspace_ids, limit: 50) { id name }
    }"""
    data = _gql(q, {"workspace_ids": [str(workspace_id)]}, token)
    for b in data.get("boards", []):
        if b["name"] == BOARD_NAME:
            return b["id"]
    return None


def _create_board(workspace_id, token):
    q = """
    mutation($name: String!, $workspace_id: ID!) {
      create_board(board_name: $name, board_kind: public, workspace_id: $workspace_id) { id }
    }"""
    data = _gql(q, {"name": BOARD_NAME, "workspace_id": str(workspace_id)}, token)
    return data["create_board"]["id"]


def _get_columns(board_id, token):
    q = """
    query($board_id: [ID!]) {
      boards(ids: $board_id) { columns { id title } }
    }"""
    data = _gql(q, {"board_id": [str(board_id)]}, token)
    boards = data.get("boards", [])
    if not boards:
        return {}
    return {c["title"]: c["id"] for c in boards[0].get("columns", [])}


def _create_column(board_id, title, col_type, token):
    q = """
    mutation($board_id: ID!, $title: String!, $type: ColumnType!) {
      create_column(board_id: $board_id, title: $title, column_type: $type) { id }
    }"""
    data = _gql(q, {"board_id": str(board_id), "title": title, "type": col_type}, token)
    return data["create_column"]["id"]


def _already_exists(board_id, place_id_col_id, place_id, token):
    """Returns True if a lead with this place_id is already on the board."""
    if not place_id or not place_id_col_id:
        return False
    q = """
    query($board_id: ID!, $col_id: String!, $val: String!) {
      items_page_by_column_values(limit: 1, board_id: $board_id,
        columns: [{column_id: $col_id, column_values: [$val]}]) {
        items { id }
      }
    }"""
    try:
        data = _gql(q, {
            "board_id": str(board_id),
            "col_id": place_id_col_id,
            "val": place_id
        }, token)
        items = data.get("items_page_by_column_values", {}).get("items", [])
        return len(items) > 0
    except Exception as e:
        logger.warning(f"Duplicate check failed for place_id {place_id}: {e}")
        return False


def get_or_create_board(workspace_id, token):
    """Returns (board_id, column_id_map). Creates board and columns if needed."""
    board_id = _find_board(workspace_id, token)
    if not board_id:
        logger.info(f"Creating '{BOARD_NAME}' board in workspace {workspace_id}")
        board_id = _create_board(workspace_id, token)

    existing = _get_columns(board_id, token)
    col_ids = dict(existing)

    for title, col_type in COLUMN_DEFS:
        if title not in existing:
            try:
                new_id = _create_column(board_id, title, col_type, token)
                col_ids[title] = new_id
                logger.info(f"Created column '{title}' on board {board_id}")
            except Exception as e:
                logger.warning(f"Could not create column '{title}': {e}")

    return board_id, col_ids


def push_lead(board_id, col_ids, lead, token):
    """
    Creates one Monday.com item from a lead dict.
    Returns (item_id, 'created') or (None, 'duplicate') if it already exists.
    """
    place_id = lead.get("place_id", "")

    # Deduplicate: skip if this place_id is already on the board
    if _already_exists(board_id, col_ids.get("Place ID"), place_id, token):
        logger.info(f"Skipping duplicate lead: {lead.get('name')} ({place_id})")
        return None, "duplicate"

    contacts = lead.get("contacts") or []
    primary = contacts[0] if contacts else {}
    contact_name = f"{primary.get('first_name','')} {primary.get('last_name','')}".strip()

    col_vals = {}

    def set_col(title, value):
        cid = col_ids.get(title)
        if cid and value:
            col_vals[cid] = value

    phone = lead.get("phone", "")
    if phone and col_ids.get("Phone"):
        digits = "".join(ch for ch in phone if ch.isdigit())
        col_vals[col_ids["Phone"]] = {"phone": digits, "countryShortName": "US"}

    website = lead.get("website", "")
    if website and col_ids.get("Website"):
        col_vals[col_ids["Website"]] = {
            "url": website,
            "text": website.replace("https://", "").replace("http://", "").rstrip("/")
        }

    set_col("Address",         lead.get("address", ""))
    set_col("Rating",          str(lead.get("rating")) if lead.get("rating") else "")
    set_col("Business Status", lead.get("business_status", "").replace("_", " "))
    set_col("Contact Name",    contact_name)
    set_col("Contact Title",   primary.get("position", ""))
    set_col("Source",          "Lead Finder")
    set_col("Place ID",        place_id)

    if contacts and contacts[0].get("email") and col_ids.get("Email"):
        e = contacts[0]["email"]
        col_vals[col_ids["Email"]] = {"email": e, "text": e}

    set_col("Email Verified",
            "Yes" if primary.get("verification_status") == "valid" else "No")

    q = """
    mutation($board_id: ID!, $name: String!, $col_vals: JSON!) {
      create_item(board_id: $board_id, item_name: $name, column_values: $col_vals) { id }
    }"""
    data = _gql(q, {
        "board_id": str(board_id),
        "name": lead.get("name", "Unknown"),
        "col_vals": json.dumps(col_vals)
    }, token)
    return data["create_item"]["id"], "created"


# ── Funnel Leads board ─────────────────────────────────────────────────────

def _find_funnel_board(workspace_id, token):
    q = """
    query($workspace_ids: [ID]) {
      boards(workspace_ids: $workspace_ids, limit: 50) { id name }
    }"""
    data = _gql(q, {"workspace_ids": [str(workspace_id)]}, token)
    for b in data.get("boards", []):
        if b["name"] == FUNNEL_BOARD:
            return b["id"]
    return None


def _find_item_by_email(board_id, email_col_id, email, token):
    """Returns item_id if a lead with this email already exists, else None."""
    if not email or not email_col_id:
        return None
    q = """
    query($board_id: ID!, $col_id: String!, $val: String!) {
      items_page_by_column_values(limit: 1, board_id: $board_id,
        columns: [{column_id: $col_id, column_values: [$val]}]) {
        items { id }
      }
    }"""
    try:
        data = _gql(q, {
            "board_id": str(board_id),
            "col_id": email_col_id,
            "val": email
        }, token)
        items = data.get("items_page_by_column_values", {}).get("items", [])
        return items[0]["id"] if items else None
    except Exception as e:
        logger.warning(f"Email duplicate check failed for {email}: {e}")
        return None


def _update_item(board_id, item_id, col_vals, token):
    q = """
    mutation($board_id: ID!, $item_id: ID!, $col_vals: JSON!) {
      change_multiple_column_values(board_id: $board_id, item_id: $item_id,
        column_values: $col_vals) { id }
    }"""
    _gql(q, {
        "board_id": str(board_id),
        "item_id":  str(item_id),
        "col_vals": json.dumps(col_vals)
    }, token)


def get_or_create_funnel_board(workspace_id, token):
    """Returns (board_id, column_id_map) for the Funnel Leads board."""
    board_id = _find_funnel_board(workspace_id, token)
    if not board_id:
        logger.info(f"Creating '{FUNNEL_BOARD}' board in workspace {workspace_id}")
        q = """
        mutation($name: String!, $workspace_id: ID!) {
          create_board(board_name: $name, board_kind: public, workspace_id: $workspace_id) { id }
        }"""
        data = _gql(q, {"name": FUNNEL_BOARD, "workspace_id": str(workspace_id)}, token)
        board_id = data["create_board"]["id"]

    existing = _get_columns(board_id, token)
    col_ids  = dict(existing)

    for title, col_type in FUNNEL_COLUMN_DEFS:
        if title not in existing:
            try:
                new_id = _create_column(board_id, title, col_type, token)
                col_ids[title] = new_id
                logger.info(f"Created funnel column '{title}' on board {board_id}")
            except Exception as e:
                logger.warning(f"Could not create funnel column '{title}': {e}")

    return board_id, col_ids


def push_funnel_lead(board_id, col_ids, lead, token):
    """
    Creates or updates a Funnel Leads Monday.com item.
    Deduplicates by email — updates existing item instead of creating a duplicate.
    Returns (item_id, 'created'|'updated').
    """
    email    = lead.get("email", "")
    name     = lead.get("name", "Unknown")
    phone    = lead.get("phone", "")
    biz_type = lead.get("biz_type", "")
    path     = lead.get("path", "")
    cpc      = lead.get("cpc", 0)
    utm      = lead.get("utm_source", "")

    col_vals = {}

    if email and col_ids.get("Email"):
        col_vals[col_ids["Email"]] = {"email": email, "text": email}

    if phone and col_ids.get("Phone"):
        digits = "".join(ch for ch in phone if ch.isdigit())
        if digits:
            col_vals[col_ids["Phone"]] = {"phone": digits, "countryShortName": "US"}

    def set_col(title, value):
        cid = col_ids.get(title)
        if cid and value:
            col_vals[cid] = str(value)

    set_col("Business Type", biz_type)
    set_col("UTM Source",    utm)
    set_col("Source",        "ROI Funnel")

    path_labels = {"ads": "Paid Ads", "overhead": "Overhead", "beginner": "Beginner"}
    set_col("Path", path_labels.get(path, path))

    if cpc and col_ids.get("Cost Per Call"):
        col_vals[col_ids["Cost Per Call"]] = cpc

    existing_id = _find_item_by_email(board_id, col_ids.get("Email"), email, token)

    if existing_id:
        _update_item(board_id, existing_id, col_vals, token)
        logger.info(f"Updated existing funnel lead: {name} ({email})")
        return existing_id, "updated"

    q = """
    mutation($board_id: ID!, $name: String!, $col_vals: JSON!) {
      create_item(board_id: $board_id, item_name: $name, column_values: $col_vals) { id }
    }"""
    data = _gql(q, {
        "board_id": str(board_id),
        "name":     name,
        "col_vals": json.dumps(col_vals)
    }, token)
    logger.info(f"Created new funnel lead: {name} ({email})")
    return data["create_item"]["id"], "created"
