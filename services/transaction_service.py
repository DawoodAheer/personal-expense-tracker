"""
Transaction Service: Manages CRUD operations and aggregations for income and expenses.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from database.db import get_connection
from utils.validators import validate_amount, validate_date, validate_non_empty


def add_transaction(
    trans_type: str,
    amount: float,
    category: str,
    payment_method: str,
    date_str: str,
    description: str = "",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a new income or expense transaction after validating inputs."""
    trans_type = trans_type.lower().strip()
    if trans_type not in ("income", "expense"):
        raise ValueError("Transaction type must be 'income' or 'expense'.")

    ok, valid_amount, msg = validate_amount(amount)
    if not ok:
        raise ValueError(msg)

    ok, valid_date, msg = validate_date(date_str)
    if not ok:
        raise ValueError(msg)

    ok, valid_cat, msg = validate_non_empty(category, "Category")
    if not ok:
        raise ValueError(msg)

    ok, valid_pm, msg = validate_non_empty(payment_method, "Payment Method")
    if not ok:
        raise ValueError(msg)

    clean_desc = (description or "").strip()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (type, amount, category, payment_method, date, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (trans_type, valid_amount, valid_cat, valid_pm, valid_date, clean_desc),
        )
        new_id = cursor.lastrowid

    return {
        "id": new_id,
        "type": trans_type,
        "amount": valid_amount,
        "category": valid_cat,
        "payment_method": valid_pm,
        "date": valid_date,
        "description": clean_desc,
    }


def get_transaction(transaction_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single transaction by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def update_transaction(
    transaction_id: int,
    trans_type: str,
    amount: float,
    category: str,
    payment_method: str,
    date_str: str,
    description: str = "",
    db_path: Optional[str] = None,
) -> bool:
    """Update an existing transaction."""
    trans_type = trans_type.lower().strip()
    if trans_type not in ("income", "expense"):
        raise ValueError("Transaction type must be 'income' or 'expense'.")

    ok, valid_amount, msg = validate_amount(amount)
    if not ok:
        raise ValueError(msg)

    ok, valid_date, msg = validate_date(date_str)
    if not ok:
        raise ValueError(msg)

    ok, valid_cat, msg = validate_non_empty(category, "Category")
    if not ok:
        raise ValueError(msg)

    ok, valid_pm, msg = validate_non_empty(payment_method, "Payment Method")
    if not ok:
        raise ValueError(msg)

    clean_desc = (description or "").strip()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE transactions
            SET type = ?, amount = ?, category = ?, payment_method = ?, date = ?, description = ?
            WHERE id = ?
            """,
            (trans_type, valid_amount, valid_cat, valid_pm, valid_date, clean_desc, transaction_id),
        )
        return cursor.rowcount > 0


def delete_transaction(transaction_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a transaction by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        return cursor.rowcount > 0


def get_all_transactions(
    trans_type: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    search_query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    month: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Retrieve filtered transactions as a pandas DataFrame."""
    sql = "SELECT id, type, amount, category, payment_method, date, description, created_at FROM transactions WHERE 1=1"
    params: List[Any] = []

    if trans_type and trans_type != "All":
        sql += " AND type = ?"
        params.append(trans_type.lower())

    if category and category != "All":
        sql += " AND category = ?"
        params.append(category)

    if payment_method and payment_method != "All":
        sql += " AND payment_method = ?"
        params.append(payment_method)

    if month:
        sql += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)

    if search_query:
        sql += " AND (description LIKE ? OR category LIKE ? OR payment_method LIKE ?)"
        q = f"%{search_query.strip()}%"
        params.extend([q, q, q])

    sql += " ORDER BY date DESC, id DESC"

    with get_connection(db_path) as conn:
        df = pd.read_sql_query(sql, conn, params=params)

    return df


def get_summary_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    month: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, float]:
    """Calculate total income, total expense, net balance, and savings rate."""
    sql = "SELECT type, COALESCE(SUM(amount), 0) as total FROM transactions WHERE 1=1"
    params: List[Any] = []

    if month:
        sql += " AND strftime('%Y-%m', date) = ?"
        params.append(month)
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)

    sql += " GROUP BY type"

    totals = {"income": 0.0, "expense": 0.0}
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        for row in cursor.fetchall():
            totals[row["type"]] = float(row["total"])

    income = totals["income"]
    expense = totals["expense"]
    balance = income - expense
    savings_rate = (balance / income * 100.0) if income > 0 else 0.0

    return {
        "total_income": round(income, 2),
        "total_expenses": round(expense, 2),
        "current_balance": round(balance, 2),
        "savings_rate": round(savings_rate, 2),
    }


def get_category_breakdown(
    trans_type: str = "expense",
    month: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Get total amount spent or received per category."""
    sql = """
        SELECT category, COALESCE(SUM(amount), 0) as total, COUNT(id) as count
        FROM transactions
        WHERE type = ?
    """
    params: List[Any] = [trans_type.lower()]
    if month:
        sql += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    sql += " GROUP BY category ORDER BY total DESC"

    with get_connection(db_path) as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    return df


def get_monthly_trend(db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve monthly aggregation of income and expenses."""
    sql = """
        SELECT 
            strftime('%Y-%m', date) AS month,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS total_expense
        FROM transactions
        GROUP BY month
        ORDER BY month ASC
    """
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(sql, conn)
    
    if not df.empty:
        df["net_savings"] = df["total_income"] - df["total_expense"]
    return df

