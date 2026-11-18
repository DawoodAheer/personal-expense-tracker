"""
Unit tests for transaction CRUD operations, filters, and financial aggregations.
"""

import os
import tempfile
import unittest
from database.db import init_db
from services.transaction_service import (
    add_transaction,
    get_transaction,
    update_transaction,
    delete_transaction,
    get_all_transactions,
    get_summary_stats,
    get_category_breakdown,
)


class TestTransactionService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tx.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_get_transaction(self):
        tx = add_transaction(
            trans_type="income",
            amount=5000.0,
            category="Salary",
            payment_method="Bank Transfer",
            date_str="2026-11-01",
            description="November Paycheck",
            db_path=self.db_path,
        )
        self.assertIsNotNone(tx["id"])
        self.assertEqual(tx["amount"], 5000.0)

        retrieved = get_transaction(tx["id"], db_path=self.db_path)
        self.assertIsNotNone(retrieved)
        assert retrieved is not None
        self.assertEqual(retrieved["category"], "Salary")
        self.assertEqual(retrieved["description"], "November Paycheck")

    def test_invalid_transaction_inputs(self):
        # Invalid amount
        with self.assertRaises(ValueError):
            add_transaction("income", -100, "Salary", "Cash", "2026-11-01", db_path=self.db_path)

        # Invalid type
        with self.assertRaises(ValueError):
            add_transaction("crypto", 100, "Salary", "Cash", "2026-11-01", db_path=self.db_path)

        # Invalid date
        with self.assertRaises(ValueError):
            add_transaction("expense", 100, "Food", "Cash", "not-a-date", db_path=self.db_path)

    def test_update_and_delete_transaction(self):
        tx = add_transaction(
            trans_type="expense",
            amount=45.50,
            category="Food & Dining",
            payment_method="Credit Card",
            date_str="2026-11-02",
            description="Dinner with friends",
            db_path=self.db_path,
        )
        tx_id = tx["id"]

        # Update
        updated = update_transaction(
            transaction_id=tx_id,
            trans_type="expense",
            amount=55.00,
            category="Food & Dining",
            payment_method="Credit Card",
            date_str="2026-11-02",
            description="Dinner with colleagues",
            db_path=self.db_path,
        )
        self.assertTrue(updated)

        refreshed = get_transaction(tx_id, db_path=self.db_path)
        self.assertIsNotNone(refreshed)
        assert refreshed is not None
        self.assertEqual(refreshed["amount"], 55.00)
        self.assertEqual(refreshed["description"], "Dinner with colleagues")

        # Delete
        deleted = delete_transaction(tx_id, db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertIsNone(get_transaction(tx_id, db_path=self.db_path))

    def test_summary_and_category_breakdown(self):
        add_transaction("income", 3000.0, "Salary", "Bank Transfer", "2026-11-01", db_path=self.db_path)
        add_transaction("expense", 500.0, "Rent & Housing", "Bank Transfer", "2026-11-02", db_path=self.db_path)
        add_transaction("expense", 200.0, "Food & Dining", "Debit Card", "2026-11-03", db_path=self.db_path)

        stats = get_summary_stats(month="2026-11", db_path=self.db_path)
        self.assertEqual(stats["total_income"], 3000.0)
        self.assertEqual(stats["total_expenses"], 700.0)
        self.assertEqual(stats["current_balance"], 2300.0)
        self.assertAlmostEqual(stats["savings_rate"], (2300.0 / 3000.0) * 100, places=1)

        breakdown = get_category_breakdown("expense", month="2026-11", db_path=self.db_path)
        self.assertEqual(len(breakdown), 2)
        top_row = breakdown.iloc[0]
        self.assertEqual(top_row["category"], "Rent & Housing")
        self.assertEqual(top_row["total"], 500.0)

    def test_filter_and_search(self):
        add_transaction("income", 1000.0, "Salary", "Bank Transfer", "2026-10-01", "Freelance Gig", db_path=self.db_path)
        add_transaction("expense", 150.0, "Groceries", "Debit Card", "2026-11-05", "Weekly groceries at Walmart", db_path=self.db_path)

        # Search query
        df_search = get_all_transactions(search_query="Walmart", db_path=self.db_path)
        self.assertEqual(len(df_search), 1)
        self.assertEqual(df_search.iloc[0]["category"], "Groceries")

        # Month filter
        df_month = get_all_transactions(month="2026-10", db_path=self.db_path)
        self.assertEqual(len(df_month), 1)
        self.assertEqual(df_month.iloc[0]["type"], "income")


if __name__ == "__main__":
    unittest.main()

