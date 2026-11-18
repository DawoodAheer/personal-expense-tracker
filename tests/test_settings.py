"""
Unit tests for Settings Service: Currency management, formatting, and zero data reset.
"""

import os
import tempfile
import unittest
from database.db import init_db
from services.transaction_service import add_transaction
from services.budget_service import set_budget
from services.settings_service import (
    get_all_currencies,
    get_active_currency,
    set_active_currency,
    reset_app_data_to_zero,
)
from utils.formatters import format_currency


class TestSettingsService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_settings.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_currencies_list(self):
        currencies = get_all_currencies()
        self.assertTrue(len(currencies) >= 20)
        codes = [c["code"] for c in currencies]
        self.assertIn("PKR", codes)
        self.assertIn("USD", codes)
        self.assertIn("INR", codes)
        self.assertIn("EUR", codes)
        self.assertIn("AED", codes)
        self.assertIn("SAR", codes)

    def test_set_and_get_currency(self):
        set_active_currency("EUR", db_path=self.db_path)
        active = get_active_currency(db_path=self.db_path)
        self.assertEqual(active["code"], "EUR")
        self.assertEqual(active["symbol"], "€")

        # Custom currency
        set_active_currency("CUSTOM", symbol="د.إ", name="Custom Dirham", position="prefix", db_path=self.db_path)
        custom = get_active_currency(db_path=self.db_path)
        self.assertEqual(custom["symbol"], "د.إ")

    def test_format_currency_with_symbols(self):
        self.assertEqual(format_currency(5000, currency_symbol="₨", position="prefix"), "₨ 5,000.00")
        self.assertEqual(format_currency(5000, currency_symbol="kr", position="suffix"), "5,000.00 kr")

    def test_reset_data_to_zero(self):
        # Add sample data
        add_transaction("income", 5000.0, "Salary", "Cash", "2026-11-01", db_path=self.db_path)
        set_budget("2026-11", "Food", 500.0, db_path=self.db_path)

        # Reset
        reset_app_data_to_zero(db_path=self.db_path)

        from services.transaction_service import get_all_transactions
        from services.budget_service import get_budgets_for_month
        self.assertEqual(len(get_all_transactions(db_path=self.db_path)), 0)
        self.assertEqual(len(get_budgets_for_month("2026-11", db_path=self.db_path)), 0)


if __name__ == "__main__":
    unittest.main()

