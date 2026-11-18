"""
Formatting utilities for currency, percentages, dates, and status badges.
Supports every world currency with dynamic prefix or suffix alignment.
"""

from typing import Union, Optional


def format_currency(
    amount: Union[float, int, None],
    currency_symbol: Optional[str] = None,
    position: Optional[str] = None,
) -> str:
    """Format a number into clean currency format with commas and two decimals.
    Supports any country's currency as prefix (e.g. ₨5,000.00, $5,000.00)
    or suffix (e.g. 5,000.00 kr).
    """
    if currency_symbol is None or position is None:
        try:
            from services.settings_service import get_active_currency
            active = get_active_currency()
            if currency_symbol is None:
                currency_symbol = active.get("symbol", "$")
            if position is None:
                position = active.get("position", "prefix")
        except Exception:
            currency_symbol = currency_symbol or "$"
            position = position or "prefix"

    symbol = currency_symbol or "$"
    pos = position or "prefix"

    if amount is None:
        return f"{symbol} 0.00" if pos == "prefix" else f"0.00 {symbol}"

    try:
        val = float(amount)
        formatted_num = f"{abs(val):,.2f}"
        if pos == "suffix":
            result = f"-{formatted_num} {symbol}" if val < 0 else f"{formatted_num} {symbol}"
        else:
            result = f"-{symbol} {formatted_num}" if val < 0 else f"{symbol} {formatted_num}"
        return result
    except (ValueError, TypeError):
        return f"{symbol} 0.00" if pos == "prefix" else f"0.00 {symbol}"


def format_percentage(val: Union[float, int, None]) -> str:
    """Format a ratio or percentage into readable XX.X%."""
    if val is None:
        return "0.0%"
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return "0.0%"
