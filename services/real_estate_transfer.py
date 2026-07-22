import os
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List
from services.real_estate_db import _db

logger = logging.getLogger(__name__)


def get_best_buyer(lead_type: str, service_area: str = None) -> Optional[dict]:
    """Return the best active buyer for this lead type, optionally filtered by area."""
    preferred_type = "wholesaler" if lead_type == "motivated_seller" else "listing_agent"
    with _db() as c:
        rows = c.execute(
            """SELECT * FROM re_buyers
               WHERE active = 1 AND type = ?
               ORDER BY fee_amount DESC, id ASC""",
            (preferred_type,),
        ).fetchall()
    if not rows:
        return None
    # Simple area match: prefer buyers whose service_areas contains the target
    if service_area:
        for r in rows:
            areas = (r["service_areas"] or "").lower()
            if service_area.lower() in areas or not areas:
                return dict(r)
    return dict(rows[0]) if rows else None


def get_all_buyers(buyer_type: str = None, active_only: bool = True) -> List[dict]:
    with _db() as c:
        query = "SELECT * FROM re_buyers WHERE 1=1"
        params: list = []
        if active_only:
            query += " AND active = 1"
        if buyer_type:
            query += " AND type = ?"
            params.append(buyer_type)
        query += " ORDER BY name ASC"
        return [dict(r) for r in c.execute(query, params).fetchall()]


def create_buyer(data: dict) -> dict:
    with _db() as c:
        cur = c.execute(
            """INSERT INTO re_buyers
               (name, company, email, phone, type, fee_amount, fee_type, buy_criteria, service_areas, active)
               VALUES (?,?,?,?,?,?,?,?,?,1)""",
            (
                data["name"],
                data.get("company"),
                data.get("email"),
                data["phone"],
                data["type"],
                data.get("fee_amount", 0),
                data.get("fee_type", "per_transfer"),
                data.get("buy_criteria"),
                data.get("service_areas"),
            ),
        )
        return {"id": cur.lastrowid, **data}


def update_buyer(buyer_id: int, data: dict) -> bool:
    fields = {k: v for k, v in data.items() if k in (
        "name", "company", "email", "phone", "type",
        "fee_amount", "fee_type", "buy_criteria", "service_areas", "active"
    )}
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    with _db() as c:
        c.execute(f"UPDATE re_buyers SET {set_clause} WHERE id = ?", [*fields.values(), buyer_id])
    return True


def record_transfer(lead_id: int, buyer_id: int, fee_amount: float,
                    method: str = "phone", notes: str = "") -> int:
    with _db() as c:
        cur = c.execute(
            """INSERT INTO re_transfers
               (lead_id, buyer_id, fee_amount, status, transfer_method, notes)
               VALUES (?,?,?,'pending',?,?)""",
            (lead_id, buyer_id, fee_amount, method, notes),
        )
        transfer_id = cur.lastrowid
        c.execute("UPDATE re_leads SET status = 'transferred' WHERE id = ?", (lead_id,))
    return transfer_id


def complete_transfer(transfer_id: int) -> bool:
    with _db() as c:
        c.execute(
            "UPDATE re_transfers SET status='completed', completed_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), transfer_id),
        )
    return True


def get_revenue_summary() -> dict:
    with _db() as c:
        row = c.execute("""
            SELECT
                COUNT(*) as total_transfers,
                SUM(CASE WHEN status='completed' THEN fee_amount ELSE 0 END) as total_revenue,
                SUM(CASE WHEN status='pending' THEN fee_amount ELSE 0 END) as pending_revenue,
                COUNT(CASE WHEN status='completed' THEN 1 END) as completed_count
            FROM re_transfers
        """).fetchone()
        leads_row = c.execute("""
            SELECT
                COUNT(*) as total_leads,
                COUNT(CASE WHEN status='qualified' THEN 1 END) as qualified,
                COUNT(CASE WHEN status='transferred' THEN 1 END) as transferred,
                COUNT(CASE WHEN lead_type='motivated_seller' THEN 1 END) as motivated_sellers,
                COUNT(CASE WHEN lead_type='buyer' THEN 1 END) as buyers
            FROM re_leads
        """).fetchone()
    return {
        "total_transfers": row["total_transfers"],
        "total_revenue": round(row["total_revenue"] or 0, 2),
        "pending_revenue": round(row["pending_revenue"] or 0, 2),
        "completed_transfers": row["completed_count"],
        "total_leads": leads_row["total_leads"],
        "qualified_leads": leads_row["qualified"],
        "transferred_leads": leads_row["transferred"],
        "motivated_sellers": leads_row["motivated_sellers"],
        "buyers": leads_row["buyers"],
    }
