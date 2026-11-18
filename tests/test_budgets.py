"""
Unit tests for Budget management, remaining budgets, and 80% / 100% threshold alert notifications.
"""

import os
import tempfile
import unittest
from database.db import init_db
from services.transaction_service import add_transaction
from services.budget_service import (
    set_budget,
    delete_budget,
    get_budget_status,
    get_budget_alert_for_expense,
)


class TestBudgetService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_budget.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_set_and_update_budget(self):
        b = set_budget(month="2026-11", category="Food & Dining", amount=500.0, db_path=self.db_path)
        self.assertEqual(b["amount"], 500.0)

        # Upsert
        b2 = set_budget(month="2026-11", category="Food & Dining", amount=600.0, db_path=self.db_path)
        self.assertEqual(b2["amount"], 600.0)

        status = get_budget_status("2026-11", db_path=self.db_path)
        self.assertEqual(len(status), 1)
        self.assertEqual(status[0]["budget"], 600.0)

    def test_budget_alert_thresholds(self):
        # Budget = 1000
        set_budget(month="2026-11", category="Shopping", amount=1000.0, db_path=self.db_path)

        # 1. Spent $500 (50%) -> SAFE
        add_transaction("expense", 500.0, "Shopping", "Credit Card", "2026-11-05", db_path=self.db_path)
        status = get_budget_status("2026-11", db_path=self.db_path)[0]
        self.assertEqual(status["alert_level"], "SAFE")
        self.assertEqual(status["remaining"], 500.0)
        self.assertEqual(status["percentage"], 50.0)

        # 2. Spent an additional $350 -> Total $850 (85%) -> WARNING (80% alert)
        add_transaction("expense", 350.0, "Shopping", "Credit Card", "2026-11-10", db_path=self.db_path)
        status = get_budget_status("2026-11", db_path=self.db_path)[0]
        self.assertEqual(status["alert_level"], "WARNING")
        self.assertEqual(status["remaining"], 150.0)
        self.assertEqual(status["percentage"], 85.0)

        # 3. Spent another $200 -> Total $1050 (105%) -> EXCEEDED (100% alert)
        add_transaction("expense", 200.0, "Shopping", "Credit Card", "2026-11-12", db_path=self.db_path)
        status = get_budget_status("2026-11", db_path=self.db_path)[0]
        self.assertEqual(status["alert_level"], "EXCEEDED")
        self.assertEqual(status["remaining"], -50.0)
        self.assertEqual(status["percentage"], 105.0)

    def test_budget_pre_check_alert(self):
        set_budget(month="2026-11", category="Entertainment", amount=100.0, db_path=self.db_path)
        add_transaction("expense", 70.0, "Entertainment", "Cash", "2026-11-01", db_path=self.db_path)

        # Adding $15 will make total $85 (85%) -> should trigger warning alert
        alerts = get_budget_alert_for_expense("Entertainment", 15.0, "2026-11-02", db_path=self.db_path)
        self.assertTrue(any("past 80%" in a for a in alerts))

        # Adding $35 will make total $105 (105%) -> should trigger exceeded alert
        alerts_exceeded = get_budget_alert_for_expense("Entertainment", 35.0, "2026-11-02", db_path=self.db_path)
        self.assertTrue(any("exceed" in a.lower() for a in alerts_exceeded))


if __name__ == "__main__":
    unittest.main()

