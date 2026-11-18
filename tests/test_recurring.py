"""
Unit tests for Recurring Transactions service.
Tests template creation, toggling active status, and auto-processing due entries.
"""

import os
import tempfile
import unittest
from datetime import date, timedelta
from database.db import init_db
from services.transaction_service import get_all_transactions
from services.recurring_service import (
    add_recurring,
    get_recurring,
    get_all_recurring,
    toggle_recurring_active,
    delete_recurring,
    process_due_recurring,
)


class TestRecurringService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_recurring.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_get_recurring(self):
        item = add_recurring(
            name="Apartment Rent",
            trans_type="expense",
            amount=1500.0,
            category="Rent & Housing",
            payment_method="Bank Transfer",
            recurrence="monthly",
            start_date="2026-11-01",
            description="Monthly apartment rent",
            db_path=self.db_path,
        )
        self.assertIsNotNone(item["id"])
        self.assertEqual(item["name"], "Apartment Rent")
        self.assertEqual(item["amount"], 1500.0)
        self.assertEqual(item["is_active"], 1)

        fetched = get_recurring(item["id"], db_path=self.db_path)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["category"], "Rent & Housing")

    def test_toggle_active_and_delete(self):
        item = add_recurring(
            name="Gym",
            trans_type="expense",
            amount=50.0,
            category="Healthcare & Fitness",
            payment_method="Credit Card",
            recurrence="monthly",
            db_path=self.db_path,
        )
        # Pause
        toggle_recurring_active(item["id"], db_path=self.db_path)
        updated = get_recurring(item["id"], db_path=self.db_path)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["is_active"], 0)

        # Resume
        toggle_recurring_active(item["id"], db_path=self.db_path)
        resumed = get_recurring(item["id"], db_path=self.db_path)
        self.assertIsNotNone(resumed)
        assert resumed is not None
        self.assertEqual(resumed["is_active"], 1)

        # Delete
        delete_recurring(item["id"], db_path=self.db_path)
        self.assertIsNone(get_recurring(item["id"], db_path=self.db_path))

    def test_process_due_recurring(self):
        # Create an entry that is due today
        today_str = date.today().isoformat()
        add_recurring(
            name="Monthly Internet",
            trans_type="expense",
            amount=60.0,
            category="Utilities",
            payment_method="Debit Card",
            recurrence="monthly",
            start_date=today_str,
            db_path=self.db_path,
        )

        # Create an entry that is due in future (should NOT be created)
        future_str = (date.today() + timedelta(days=15)).isoformat()
        add_recurring(
            name="Future Streaming",
            trans_type="expense",
            amount=15.0,
            category="Entertainment",
            payment_method="Credit Card",
            recurrence="monthly",
            start_date=future_str,
            db_path=self.db_path,
        )

        # Process due entries
        created = process_due_recurring(db_path=self.db_path)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]["recurring_name"], "Monthly Internet")

        # Verify transaction was recorded in transactions table
        txs = get_all_transactions(db_path=self.db_path)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs.iloc[0]["amount"], 60.0)

        # Calling process_due_recurring again should not create duplicate since next_due_date advanced
        again = process_due_recurring(db_path=self.db_path)
        self.assertEqual(len(again), 0)


if __name__ == "__main__":
    unittest.main()
