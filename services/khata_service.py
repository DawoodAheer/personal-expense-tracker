"""
Smart Khata & Hisaab Service: Parse natural language daily hisaab notes,
calculate mathematical sums and differences (e.g. 200 Chicken + 500 Cash - 100),
and permanently store monthly calculations in SQLite.
"""

import re
import json
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
from database.db import get_connection


def parse_hisaab_chunk(chunk: str, sign: int) -> Optional[Dict[str, Any]]:
    """Parse a single text item chunk into amount, label, and signed value."""
    cleaned = chunk.strip()
    if not cleaned:
        return None

    # Search for first number (integer or float, commas allowed like 1,000)
    match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)", cleaned)
    if not match:
        return None

    num_str = match.group(1).replace(",", "")
    try:
        amount = float(num_str)
    except ValueError:
        return None

    # Description is the rest of the text without the number and equal signs
    start_idx, end_idx = match.span()
    label = (cleaned[:start_idx] + " " + cleaned[end_idx:]).strip()
    label = re.sub(r"[=:;,]+", " ", label).strip()

    if not label:
        label = "Item" if sign > 0 else "Deduction"

    signed_amount = amount * sign

    return {
        "label": label,
        "amount": round(amount, 2),
        "sign": sign,  # +1 or -1
        "signed_amount": round(signed_amount, 2),
        "type": "add" if sign > 0 else "deduct",
    }


def parse_hisaab_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse a complete hisaab note text (single or multi-line) and return
    structured breakdown items and accurate mathematical total.

    Handles expressions such as:
      - '200 Chicken + 500 Cash = 700'
      - '200 Chicken + 300 Cash + 400 daal - 100 - 20 aloo Sabzii'
      - Multi-line notes with + and - items
    """
    if not raw_text or not raw_text.strip():
        return {
            "items": [],
            "total_additions": 0.0,
            "total_deductions": 0.0,
            "net_total": 0.0,
            "item_count": 0,
        }

    items: List[Dict[str, Any]] = []

    # Process line by line
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Ignore everything after '=' if the user typed an answer himself
        if "=" in line:
            line = line.split("=")[0].strip()

        # Tokenize line by '+' and '-' while preserving the operators
        # Regex splits on '+' or '-' preceded by space or start, keeping delimiter
        tokens = re.split(r"(?<=\S)(?=[+-])|(?<=[+-])(?=\S)|(?<=\s)(?=[+-])", line)

        current_sign = 1
        current_chunk = ""

        # Simpler robust regex tokenization: find all (+|-)?([^+-\n]+)
        # Using regex to find signed segments
        pattern = re.compile(r"([+-]?)\s*([^+\-]+)")
        matches = pattern.findall(line)

        for op, text_part in matches:
            text_part = text_part.strip()
            if not text_part:
                continue

            op = op.strip()
            sign = -1 if op == "-" else 1
            parsed = parse_hisaab_chunk(text_part, sign)
            if parsed:
                items.append(parsed)

    total_add = sum(item["amount"] for item in items if item["sign"] > 0)
    total_ded = sum(item["amount"] for item in items if item["sign"] < 0)
    net_total = total_add - total_ded

    return {
        "items": items,
        "total_additions": round(total_add, 2),
        "total_deductions": round(total_ded, 2),
        "net_total": round(net_total, 2),
        "item_count": len(items),
    }


def save_khata_note(
    title: str,
    raw_text: str,
    date_str: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Save a parsed hisaab note into the database."""
    title_clean = (title or "").strip() or "Untitled Hisaab Note"
    calc = parse_hisaab_text(raw_text)

    d_str = date_str if date_str else date.today().isoformat()
    month_str = d_str[:7]  # YYYY-MM

    breakdown_json = json.dumps(calc["items"])

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO khata_notes (title, month, date, raw_text, calculated_total, breakdown_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title_clean, month_str, d_str, raw_text.strip(), calc["net_total"], breakdown_json),
        )
        new_id = cursor.lastrowid

    return get_khata_note(new_id, db_path=db_path)  # type: ignore[return-value]


def get_khata_note(note_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single khata note by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM khata_notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            try:
                d["items"] = json.loads(d.get("breakdown_json") or "[]")
            except Exception:
                d["items"] = []
            return d
    return None


def get_all_khata_notes(
    month: Optional[str] = None,
    search_query: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve saved notes filtered by month or keyword."""
    sql = "SELECT * FROM khata_notes WHERE 1=1"
    params: List[Any] = []

    if month and month != "All Months":
        sql += " AND month = ?"
        params.append(month)

    if search_query:
        sql += " AND (title LIKE ? OR raw_text LIKE ?)"
        q = f"%{search_query.strip()}%"
        params.extend([q, q])

    sql += " ORDER BY date DESC, id DESC"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    results: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        try:
            d["items"] = json.loads(d.get("breakdown_json") or "[]")
        except Exception:
            d["items"] = []
        results.append(d)
    return results


def update_khata_note(
    note_id: int,
    title: str,
    raw_text: str,
    date_str: str,
    db_path: Optional[str] = None,
) -> bool:
    """Update an existing khata note."""
    calc = parse_hisaab_text(raw_text)
    month_str = date_str[:7]
    breakdown_json = json.dumps(calc["items"])

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE khata_notes
            SET title = ?, month = ?, date = ?, raw_text = ?, calculated_total = ?, breakdown_json = ?
            WHERE id = ?
            """,
            (title.strip(), month_str, date_str, raw_text.strip(), calc["net_total"], breakdown_json, note_id),
        )
        return cursor.rowcount > 0


def delete_khata_note(note_id: int, db_path: Optional[str] = None) -> bool:
    """Permanently delete a khata note."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM khata_notes WHERE id = ?", (note_id,))
        return cursor.rowcount > 0

