"""
Settings Service: Manages global multi-currency configuration for all world countries,
persistent user preferences, and clean database zero-resetting.
"""

from typing import Dict, Any, List, Optional
from database.db import get_setting, set_setting, reset_database_to_zero

# Comprehensive World Currencies Registry
WORLD_CURRENCIES: List[Dict[str, Any]] = [
    {"code": "PKR", "symbol": "₨", "name": "Pakistani Rupee", "country": "Pakistan 🇵🇰", "position": "prefix"},
    {"code": "INR", "symbol": "₹", "name": "Indian Rupee", "country": "India 🇮🇳", "position": "prefix"},
    {"code": "USD", "symbol": "$", "name": "US Dollar", "country": "United States 🇺🇸", "position": "prefix"},
    {"code": "EUR", "symbol": "€", "name": "Euro", "country": "European Union 🇪🇺", "position": "prefix"},
    {"code": "GBP", "symbol": "£", "name": "British Pound", "country": "United Kingdom 🇬🇧", "position": "prefix"},
    {"code": "AED", "symbol": "AED", "name": "UAE Dirham", "country": "United Arab Emirates 🇦🇪", "position": "prefix"},
    {"code": "SAR", "symbol": "SAR", "name": "Saudi Riyal", "country": "Saudi Arabia 🇸🇦", "position": "prefix"},
    {"code": "CAD", "symbol": "CA$", "name": "Canadian Dollar", "country": "Canada 🇨🇦", "position": "prefix"},
    {"code": "AUD", "symbol": "AU$", "name": "Australian Dollar", "country": "Australia 🇦🇺", "position": "prefix"},
    {"code": "TRY", "symbol": "₺", "name": "Turkish Lira", "country": "Turkey 🇹🇷", "position": "prefix"},
    {"code": "BDT", "symbol": "৳", "name": "Bangladeshi Taka", "country": "Bangladesh 🇧🇩", "position": "prefix"},
    {"code": "JPY", "symbol": "¥", "name": "Japanese Yen", "country": "Japan 🇯🇵", "position": "prefix"},
    {"code": "CNY", "symbol": "¥", "name": "Chinese Yuan", "country": "China 🇨🇳", "position": "prefix"},
    {"code": "CHF", "symbol": "CHF", "name": "Swiss Franc", "country": "Switzerland 🇨🇭", "position": "prefix"},
    {"code": "SGD", "symbol": "S$", "name": "Singapore Dollar", "country": "Singapore 🇸🇬", "position": "prefix"},
    {"code": "MYR", "symbol": "RM", "name": "Malaysian Ringgit", "country": "Malaysia 🇲🇾", "position": "prefix"},
    {"code": "QAR", "symbol": "QAR", "name": "Qatari Riyal", "country": "Qatar 🇶🇦", "position": "prefix"},
    {"code": "KWD", "symbol": "KWD", "name": "Kuwaiti Dinar", "country": "Kuwait 🇰🇼", "position": "prefix"},
    {"code": "OMR", "symbol": "OMR", "name": "Omani Rial", "country": "Oman 🇴🇲", "position": "prefix"},
    {"code": "BHD", "symbol": "BHD", "name": "Bahraini Dinar", "country": "Bahrain 🇧🇭", "position": "prefix"},
    {"code": "EGP", "symbol": "E£", "name": "Egyptian Pound", "country": "Egypt 🇪🇬", "position": "prefix"},
    {"code": "NGN", "symbol": "₦", "name": "Nigerian Naira", "country": "Nigeria 🇳🇬", "position": "prefix"},
    {"code": "ZAR", "symbol": "R", "name": "South African Rand", "country": "South Africa 🇿🇦", "position": "prefix"},
    {"code": "BRL", "symbol": "R$", "name": "Brazilian Real", "country": "Brazil 🇧🇷", "position": "prefix"},
    {"code": "RUB", "symbol": "₽", "name": "Russian Ruble", "country": "Russia 🇷🇺", "position": "prefix"},
    {"code": "KRW", "symbol": "₩", "name": "South Korean Won", "country": "South Korea 🇰🇷", "position": "prefix"},
    {"code": "IDR", "symbol": "Rp", "name": "Indonesian Rupiah", "country": "Indonesia 🇮🇩", "position": "prefix"},
    {"code": "LKR", "symbol": "Rs", "name": "Sri Lankan Rupee", "country": "Sri Lanka 🇱🇰", "position": "prefix"},
    {"code": "NPR", "symbol": "Rs", "name": "Nepalese Rupee", "country": "Nepal 🇳🇵", "position": "prefix"},
    {"code": "AFN", "symbol": "؋", "name": "Afghan Afghani", "country": "Afghanistan 🇦🇫", "position": "prefix"},
    {"code": "PHP", "symbol": "₱", "name": "Philippine Peso", "country": "Philippines 🇵🇭", "position": "prefix"},
    {"code": "MXN", "symbol": "MX$", "name": "Mexican Peso", "country": "Mexico 🇲🇽", "position": "prefix"},
    {"code": "NZD", "symbol": "NZ$", "name": "New Zealand Dollar", "country": "New Zealand 🇳🇿", "position": "prefix"},
    {"code": "SEK", "symbol": "kr", "name": "Swedish Krona", "country": "Sweden 🇸🇪", "position": "suffix"},
    {"code": "NOK", "symbol": "kr", "name": "Norwegian Krone", "country": "Norway 🇳🇴", "position": "suffix"},
    {"code": "DKK", "symbol": "kr", "name": "Danish Krone", "country": "Denmark 🇩🇰", "position": "suffix"},
    {"code": "CUSTOM", "symbol": "¤", "name": "Custom Currency", "country": "Custom / Other 🌐", "position": "prefix"},
]

DEFAULT_CURRENCY_CODE = "PKR"  # Defaults to PKR as requested, user can switch to ANY currency


def get_all_currencies() -> List[Dict[str, Any]]:
    """Return list of all supported world currencies."""
    return WORLD_CURRENCIES


def get_active_currency(db_path: Optional[str] = None) -> Dict[str, str]:
    """Retrieve active currency configuration from settings or default."""
    code = get_setting("currency_code", default=DEFAULT_CURRENCY_CODE, db_path=db_path)
    symbol = get_setting("currency_symbol", default="", db_path=db_path)
    name = get_setting("currency_name", default="", db_path=db_path)
    position = get_setting("currency_position", default="prefix", db_path=db_path)

    # Match from registry if not custom
    matched = next((c for c in WORLD_CURRENCIES if c["code"] == code), None)
    if matched and not symbol:
        symbol = matched["symbol"]
        name = matched["name"]
        position = matched.get("position", "prefix")
    elif not symbol:
        symbol = "₨" if code == "PKR" else "$"
        name = code
        position = "prefix"

    return {
        "code": code,
        "symbol": symbol,
        "name": name,
        "position": position,
    }


def set_active_currency(
    code: str,
    symbol: Optional[str] = None,
    name: Optional[str] = None,
    position: str = "prefix",
    db_path: Optional[str] = None,
) -> None:
    """Save user's chosen currency into persistent settings."""
    code_clean = code.strip().upper()
    matched = next((c for c in WORLD_CURRENCIES if c["code"] == code_clean), None)

    final_symbol = symbol.strip() if symbol else (matched["symbol"] if matched else code_clean)
    final_name = name.strip() if name else (matched["name"] if matched else code_clean)
    final_pos = position if position in ("prefix", "suffix") else "prefix"

    set_setting("currency_code", code_clean, db_path=db_path)
    set_setting("currency_symbol", final_symbol, db_path=db_path)
    set_setting("currency_name", final_name, db_path=db_path)
    set_setting("currency_position", final_pos, db_path=db_path)


def get_theme(db_path: Optional[str] = None) -> str:
    """Retrieve user interface theme (light or dark). Default is light."""
    theme = get_setting("app_theme", default="light", db_path=db_path)
    return "dark" if theme.lower() == "dark" else "light"


def set_theme(theme: str, db_path: Optional[str] = None) -> None:
    """Save user interface theme preference."""
    clean_theme = "dark" if theme.lower() == "dark" else "light"
    set_setting("app_theme", clean_theme, db_path=db_path)


def reset_app_data_to_zero(db_path: Optional[str] = None) -> None:
    """Completely wipe all transaction, budget, goal, and recurring records so user starts fresh from 0."""
    reset_database_to_zero(db_path=db_path)

