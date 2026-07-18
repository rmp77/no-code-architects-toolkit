import json
import requests
import logging

logger = logging.getLogger(__name__)

MONDAY_API = "https://api.monday.com/v2"
BOARD_NAME = "Leads"

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
    query($workspace_id: [ID]) {
      boards(workspace_id: $workspace_id, limit: 50) { id name }
    }"""
    data = _gql(q, {"workspace_id": [str(workspace_id)]}, token)
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
