"""
Goals Service: Manage financial saving goals — create, update progress,
complete, and delete personal money targets.
"""

from typing import List, Dict, Any, Optional
from database.db import get_connection


def add_goal(
    name: str,
    target_amount: float,
    category: str = "General",
    deadline: Optional[str] = None,
    description: str = "",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new financial savings goal."""
    name = name.strip()
    if not name:
        raise ValueError("Goal name cannot be empty.")
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than zero.")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO goals (name, target_amount, saved_amount, category, deadline, description)
            VALUES (?, ?, 0, ?, ?, ?)
            """,
            (name, round(target_amount, 2), category.strip(), deadline, description.strip()),
        )
        new_id = cursor.lastrowid

    return get_goal(new_id, db_path=db_path)  # type: ignore[return-value]


def get_goal(goal_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single goal by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        row = cursor.fetchone()
        if row:
            return _enrich_goal(dict(row))
    return None


def get_all_goals(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all goals, active ones first then completed."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM goals ORDER BY is_completed ASC, created_at DESC"
        )
        rows = cursor.fetchall()
    return [_enrich_goal(dict(r)) for r in rows]


def update_goal_savings(
    goal_id: int,
    new_saved_amount: float,
    db_path: Optional[str] = None,
) -> bool:
    """Set the total saved amount for a goal and auto-mark as complete if target met."""
    if new_saved_amount < 0:
        raise ValueError("Saved amount cannot be negative.")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Auto-complete when saved >= target
        cursor.execute(
            """
            UPDATE goals
            SET saved_amount = ?,
                is_completed = CASE WHEN ? >= target_amount THEN 1 ELSE 0 END
            WHERE id = ?
            """,
            (round(new_saved_amount, 2), round(new_saved_amount, 2), goal_id),
        )
        return cursor.rowcount > 0


def add_to_goal_savings(
    goal_id: int,
    amount: float,
    db_path: Optional[str] = None,
) -> bool:
    """Add a contribution amount to a goal's saved total."""
    if amount <= 0:
        raise ValueError("Contribution amount must be positive.")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE goals
            SET saved_amount = MIN(saved_amount + ?, target_amount),
                is_completed = CASE WHEN saved_amount + ? >= target_amount THEN 1 ELSE 0 END
            WHERE id = ?
            """,
            (round(amount, 2), round(amount, 2), goal_id),
        )
        return cursor.rowcount > 0


def delete_goal(goal_id: int, db_path: Optional[str] = None) -> bool:
    """Permanently delete a goal."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        return cursor.rowcount > 0


def reset_goal(goal_id: int, db_path: Optional[str] = None) -> bool:
    """Reset a goal's saved amount back to 0 (un-complete it)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE goals SET saved_amount = 0, is_completed = 0 WHERE id = ?",
            (goal_id,),
        )
        return cursor.rowcount > 0


def _enrich_goal(goal: Dict[str, Any]) -> Dict[str, Any]:
    """Add computed fields: percentage, remaining, days_left, status."""
    target = float(goal.get("target_amount") or 0)
    saved = float(goal.get("saved_amount") or 0)

    pct = min((saved / target * 100.0) if target > 0 else 0.0, 100.0)
    remaining = max(target - saved, 0.0)

    # Days left calculation
    days_left: Optional[int] = None
    deadline = goal.get("deadline")
    if deadline:
        try:
            from datetime import date
            dl = date.fromisoformat(str(deadline))
            days_left = (dl - date.today()).days
        except (ValueError, TypeError):
            days_left = None

    # Status label
    if goal.get("is_completed") or saved >= target:
        status = "ACHIEVED"
    elif days_left is not None and days_left < 0:
        status = "OVERDUE"
    elif days_left is not None and days_left <= 30:
        status = "URGENT"
    else:
        status = "IN_PROGRESS"

    goal["percentage"] = round(pct, 2)
    goal["remaining"] = round(remaining, 2)
    goal["days_left"] = days_left
    goal["status"] = status
    return goal

