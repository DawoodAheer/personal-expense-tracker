"""
Recurring Transactions Service: Manage repeating income/expense entries
(monthly rent, salary, bills). Auto-generates due entries on app startup.
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from database.db import get_connection
from services.transaction_service import add_transaction


def add_recurring(
    name: str,
    trans_type: str,
    amount: float,
    category: str,
    payment_method: str,
    recurrence: str = "monthly",
    start_date: Optional[str] = None,
    description: str = "",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a recurring transaction template."""
    name = name.strip()
    if not name:
        raise ValueError("Recurring transaction name cannot be empty.")
    trans_type = trans_type.lower().strip()
    if trans_type not in ("income", "expense"):
        raise ValueError("Type must be 'income' or 'expense'.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if recurrence not in ("daily", "weekly", "monthly"):
        raise ValueError("Recurrence must be daily, weekly, or monthly.")

    # Default start: today
    next_due = start_date if start_date else date.today().isoformat()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO recurring_transactions
                (name, type, amount, category, payment_method, recurrence, next_due_date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                trans_type,
                round(amount, 2),
                category.strip(),
                payment_method.strip(),
                recurrence,
                next_due,
                description.strip(),
            ),
        )
        new_id = cursor.lastrowid

    return get_recurring(new_id, db_path=db_path)  # type: ignore[return-value]


def get_recurring(rec_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single recurring transaction by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recurring_transactions WHERE id = ?", (rec_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_all_recurring(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all recurring transactions sorted by name."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM recurring_transactions ORDER BY is_active DESC, name ASC"
        )
        return [dict(r) for r in cursor.fetchall()]


def toggle_recurring_active(rec_id: int, db_path: Optional[str] = None) -> bool:
    """Toggle a recurring transaction between active and paused."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE recurring_transactions SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (rec_id,),
        )
        return cursor.rowcount > 0


def delete_recurring(rec_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a recurring transaction template."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recurring_transactions WHERE id = ?", (rec_id,))
        return cursor.rowcount > 0


def _advance_next_due(current_due: str, recurrence: str) -> str:
    """Calculate the next due date after the current one."""
    try:
        d = date.fromisoformat(current_due)
    except ValueError:
        d = date.today()

    if recurrence == "daily":
        d += timedelta(days=1)
    elif recurrence == "weekly":
        d += timedelta(weeks=1)
    else:  # monthly
        # Advance by one month safely (handle month-end edge cases)
        month = d.month + 1
        year = d.year
        if month > 12:
            month = 1
            year += 1
        # Clamp day to last day of new month
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        day = min(d.day, last_day)
        d = date(year, month, day)

    return d.isoformat()


def process_due_recurring(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Check all active recurring transactions and auto-create any that are due today or overdue.
    Returns a list of transactions that were auto-created.
    Called on every app startup — safe to call repeatedly (uses next_due_date guard).
    """
    today_str = date.today().isoformat()
    created_entries: List[Dict[str, Any]] = []

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM recurring_transactions
            WHERE is_active = 1 AND next_due_date <= ?
            ORDER BY next_due_date ASC
            """,
            (today_str,),
        )
        due_items = [dict(r) for r in cursor.fetchall()]

    for item in due_items:
        # Create the actual transaction
        try:
            tx = add_transaction(
                trans_type=item["type"],
                amount=float(item["amount"]),
                category=item["category"],
                payment_method=item["payment_method"],
                date_str=item["next_due_date"],
                description=f"[Auto] {item['name']}: {item.get('description', '')}".strip(": "),
                db_path=db_path,
            )
            # Advance next_due_date to the next period
            new_due = _advance_next_due(item["next_due_date"], item["recurrence"])
            with get_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE recurring_transactions SET next_due_date = ? WHERE id = ?",
                    (new_due, item["id"]),
                )
            created_entries.append({
                "recurring_name": item["name"],
                "transaction": tx,
                "next_due": new_due,
            })
        except Exception:
            # Never let recurring processing crash the app
            pass

    return created_entries

