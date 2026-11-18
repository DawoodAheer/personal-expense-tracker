"""
Input validation utilities for Personal Expense Tracker.
"""

from datetime import datetime, date
from typing import Tuple, Optional


def validate_amount(amount_val) -> Tuple[bool, Optional[float], str]:
    """Validate that amount is a positive number."""
    if amount_val is None:
        return False, None, "Amount is required."
    try:
        val = float(amount_val)
        if val <= 0:
            return False, None, "Amount must be greater than zero."
        if val > 1_000_000_000:
            return False, None, "Amount exceeds realistic limits."
        return True, round(val, 2), ""
    except (ValueError, TypeError):
        return False, None, "Invalid amount format. Please enter a valid number."


def validate_date(date_val) -> Tuple[bool, Optional[str], str]:
    """Validate that date is provided and formatted as YYYY-MM-DD."""
    if date_val is None:
        return False, None, "Date is required."
    if isinstance(date_val, (datetime, date)):
        return True, date_val.strftime("%Y-%m-%d"), ""
    if isinstance(date_val, str):
        try:
            dt = datetime.strptime(date_val.strip(), "%Y-%m-%d")
            return True, dt.strftime("%Y-%m-%d"), ""
        except ValueError:
            return False, None, "Date must be in YYYY-MM-DD format."
    return False, None, "Invalid date format."


def validate_month(month_val: str) -> Tuple[bool, Optional[str], str]:
    """Validate that month string is in YYYY-MM format."""
    if not month_val or not isinstance(month_val, str):
        return False, None, "Month is required."
    try:
        dt = datetime.strptime(month_val.strip(), "%Y-%m")
        return True, dt.strftime("%Y-%m"), ""
    except ValueError:
        return False, None, "Month must be in YYYY-MM format (e.g. 2026-11)."


def validate_non_empty(val: str, field_name: str) -> Tuple[bool, str, str]:
    """Validate that a string field is not empty."""
    if not val or not val.strip():
        return False, "", f"{field_name} cannot be empty."
    return True, val.strip(), ""

