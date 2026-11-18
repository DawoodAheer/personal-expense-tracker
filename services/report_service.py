"""
Report Service: Computes monthly summaries, previous-month comparisons, and deep spending analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import pandas as pd
from database.db import get_connection


def get_available_months(db_path: Optional[str] = None) -> List[str]:
    """Retrieve all unique YYYY-MM months present in transactions."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT strftime('%Y-%m', date) AS month FROM transactions ORDER BY month DESC")
        months = [row["month"] for row in cursor.fetchall() if row["month"]]

    current_month = date.today().strftime("%Y-%m")
    if current_month not in months:
        months.insert(0, current_month)
    return months


def get_previous_month(month_str: str) -> str:
    """Compute the YYYY-MM of the preceding month."""
    dt = datetime.strptime(month_str + "-01", "%Y-%m-%d")
    year = dt.year
    month = dt.month
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1
    return f"{prev_year:04d}-{prev_month:02d}"


def get_monthly_summary(month: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculate comprehensive statistics for a specific month."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Income, Expense, Count
        cursor.execute(
            """
            SELECT 
                type, 
                COALESCE(SUM(amount), 0) AS total,
                COUNT(id) AS count
            FROM transactions
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY type
            """,
            (month,),
        )
        totals = {"income": 0.0, "expense": 0.0, "income_count": 0, "expense_count": 0}
        for row in cursor.fetchall():
            t = row["type"]
            totals[t] = float(row["total"])
            totals[f"{t}_count"] = int(row["count"])

        # Category spending breakdown
        cursor.execute(
            """
            SELECT category, SUM(amount) AS total, COUNT(id) AS count
            FROM transactions
            WHERE type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (month,),
        )
        cat_rows = [dict(r) for r in cursor.fetchall()]

        # Daily spending
        cursor.execute(
            """
            SELECT date, SUM(amount) AS total
            FROM transactions
            WHERE type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY date
            ORDER BY total DESC
            LIMIT 1
            """,
            (month,),
        )
        peak_day_row = cursor.fetchone()

        # Distinct expense days count for daily average
        cursor.execute(
            """
            SELECT COUNT(DISTINCT date) AS active_days
            FROM transactions
            WHERE type = 'expense' AND strftime('%Y-%m', date) = ?
            """,
            (month,),
        )
        active_days_row = cursor.fetchone()
        active_days = int(active_days_row["active_days"]) if active_days_row and active_days_row["active_days"] else 0

        # Payment methods breakdown
        cursor.execute(
            """
            SELECT payment_method, SUM(amount) AS total, COUNT(id) AS count
            FROM transactions
            WHERE type = 'expense' AND strftime('%Y-%m', date) = ?
            GROUP BY payment_method
            ORDER BY total DESC
            """,
            (month,),
        )
        pm_rows = [dict(r) for r in cursor.fetchall()]

    income = totals["income"]
    expense = totals["expense"]
    balance = income - expense
    savings_rate = (balance / income * 100.0) if income > 0 else 0.0

    top_category = cat_rows[0]["category"] if cat_rows else "None"
    top_cat_amount = float(cat_rows[0]["total"]) if cat_rows else 0.0
    top_cat_pct = (top_cat_amount / expense * 100.0) if expense > 0 else 0.0

    peak_day = peak_day_row["date"] if peak_day_row else "None"
    peak_day_amount = float(peak_day_row["total"]) if peak_day_row else 0.0

    # Calculate daily average based on distinct days with expenses
    daily_avg = (expense / active_days) if active_days > 0 else 0.0

    return {
        "month": month,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net_savings": round(balance, 2),
        "savings_rate": round(savings_rate, 1),
        "income_count": totals["income_count"],
        "expense_count": totals["expense_count"],
        "total_transactions": totals["income_count"] + totals["expense_count"],
        "top_category": top_category,
        "top_category_amount": round(top_cat_amount, 2),
        "top_category_pct": round(top_cat_pct, 1),
        "peak_spending_day": peak_day,
        "peak_spending_amount": round(peak_day_amount, 2),
        "daily_average": round(daily_avg, 2),
        "category_breakdown": cat_rows,
        "payment_method_breakdown": pm_rows,
    }


def get_monthly_comparison(current_month: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Compare the selected month with the prior month."""
    prev_month = get_previous_month(current_month)

    cur_stats = get_monthly_summary(current_month, db_path=db_path)
    prev_stats = get_monthly_summary(prev_month, db_path=db_path)

    def calc_delta(cur, prev):
        diff = cur - prev
        pct_diff = ((diff / prev) * 100.0) if prev > 0 else (100.0 if cur > 0 else 0.0)
        return round(diff, 2), round(pct_diff, 1)

    income_diff, income_pct_diff = calc_delta(cur_stats["income"], prev_stats["income"])
    expense_diff, expense_pct_diff = calc_delta(cur_stats["expense"], prev_stats["expense"])
    savings_diff, savings_pct_diff = calc_delta(cur_stats["net_savings"], prev_stats["net_savings"])

    # Category level changes
    prev_cats = {row["category"]: row["total"] for row in prev_stats["category_breakdown"]}
    cur_cats = {row["category"]: row["total"] for row in cur_stats["category_breakdown"]}
    all_cats = sorted(set(list(prev_cats.keys()) + list(cur_cats.keys())))

    category_changes = []
    for cat in all_cats:
        c_val = cur_cats.get(cat, 0.0)
        p_val = prev_cats.get(cat, 0.0)
        diff, pct = calc_delta(c_val, p_val)
        category_changes.append({
            "category": cat,
            "current_month": round(c_val, 2),
            "prev_month": round(p_val, 2),
            "difference": diff,
            "pct_change": pct,
        })

    return {
        "current_month": current_month,
        "previous_month": prev_month,
        "current": cur_stats,
        "previous": prev_stats,
        "income_delta": income_diff,
        "income_pct_delta": income_pct_diff,
        "expense_delta": expense_diff,
        "expense_pct_delta": expense_pct_diff,
        "savings_delta": savings_diff,
        "savings_pct_delta": savings_pct_diff,
        "category_changes": category_changes,
    }
