"""
Budget Service: Manages budget limits, remaining calculations, and 80%/100% alert triggers.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from database.db import get_connection
from utils.validators import validate_amount, validate_month, validate_non_empty
from utils.formatters import format_currency


def set_budget(
    month: str,
    category: str,
    amount: float,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Set or update a budget for a given month and category (e.g., 'Overall' or specific category)."""
    ok, valid_month, msg = validate_month(month)
    if not ok:
        raise ValueError(msg)

    ok, valid_amount, msg = validate_amount(amount)
    if not ok:
        raise ValueError(msg)

    ok, valid_cat, msg = validate_non_empty(category, "Category")
    if not ok:
        raise ValueError(msg)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO budgets (month, category, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, category) DO UPDATE SET amount = excluded.amount
            """,
            (valid_month, valid_cat, valid_amount),
        )
        budget_id = cursor.lastrowid

    return {
        "id": budget_id,
        "month": valid_month,
        "category": valid_cat,
        "amount": valid_amount,
    }


def delete_budget(budget_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a budget entry by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        return cursor.rowcount > 0


def get_budgets_for_month(month: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all budget configurations for a specific month."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, month, category, amount FROM budgets WHERE month = ? ORDER BY category ASC",
            (month,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_budget_status(month: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Compare budgets with actual expenses for a given month.
    Returns status objects containing budget, spent, remaining, percentage, and alert level.
    Alert levels:
      - 'EXCEEDED': spent >= 100% of budget (Red alert)
      - 'WARNING': spent >= 80% and < 100% of budget (Yellow/Orange alert)
      - 'SAFE': spent < 80% of budget (Green)
    """
    budgets = get_budgets_for_month(month, db_path=db_path)
    if not budgets:
        return []

    # Get actual spending by category for this month
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Spending by category
        cursor.execute(
            """
            SELECT category, COALESCE(SUM(amount), 0) AS total_spent
            FROM transactions
            WHERE type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category
            """,
            (month,),
        )
        cat_spending = {row["category"]: float(row["total_spent"]) for row in cursor.fetchall()}

        # Total overall spending for the month
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_spent
            FROM transactions
            WHERE type = 'expense' AND strftime('%Y-%m', date) = ?
            """,
            (month,),
        )
        row = cursor.fetchone()
        total_monthly_spending = float(row["total_spent"]) if row else 0.0

    statuses = []
    for b in budgets:
        cat = b["category"]
        budget_amt = float(b["amount"])

        if cat.lower() == "overall":
            spent = total_monthly_spending
        else:
            spent = cat_spending.get(cat, 0.0)

        remaining = budget_amt - spent
        pct = (spent / budget_amt * 100.0) if budget_amt > 0 else 0.0

        if pct >= 100.0:
            alert_level = "EXCEEDED"
            alert_message = f"Budget for '{cat}' has been exceeded by {format_currency(abs(remaining))} ({pct:.1f}% used)!"
        elif pct >= 80.0:
            alert_level = "WARNING"
            alert_message = f"Warning: '{cat}' budget has reached {pct:.1f}% ({format_currency(spent)} of {format_currency(budget_amt)})."
        else:
            alert_level = "SAFE"
            alert_message = f"Healthy: {pct:.1f}% used ({format_currency(remaining)} remaining)."

        statuses.append({
            "id": b["id"],
            "month": month,
            "category": cat,
            "budget": round(budget_amt, 2),
            "spent": round(spent, 2),
            "remaining": round(remaining, 2),
            "percentage": round(pct, 1),
            "alert_level": alert_level,
            "alert_message": alert_message,
        })

    return statuses


def get_budget_alert_for_expense(
    category: str,
    amount: float,
    date_str: str,
    db_path: Optional[str] = None,
) -> List[str]:
    """
    Check if adding a specific expense will trigger an 80% or 100% budget alert
    for the category or overall monthly budget.
    """
    alerts = []
    month = date_str[:7]
    statuses = get_budget_status(month, db_path=db_path)

    for s in statuses:
        if s["category"].lower() in (category.lower(), "overall"):
            new_spent = s["spent"] + amount
            new_pct = (new_spent / s["budget"] * 100.0) if s["budget"] > 0 else 0.0

            if new_pct >= 100.0:
                alerts.append(
                    f"Adding this will exceed the {s['category']} budget! ({new_pct:.1f}% of {format_currency(s['budget'])})"
                )
            elif new_pct >= 80.0:
                alerts.append(
                    f"Adding this will push {s['category']} budget past 80%! ({new_pct:.1f}% of {format_currency(s['budget'])})"
                )

    return alerts

