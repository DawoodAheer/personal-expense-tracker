"""
Unit tests for database initialization, schema, and connection management.
"""

import os
import tempfile
import unittest
from database.db import init_db, get_connection


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tracker.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tables_created(self):
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row["name"] for row in cursor.fetchall()}
            self.assertIn("transactions", tables)
            self.assertIn("budgets", tables)

    def test_transaction_check_constraints(self):
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            # Invalid type should fail
            with self.assertRaises(Exception):
                cursor.execute(
                    "INSERT INTO transactions (type, amount, category, payment_method, date) VALUES ('invalid', 100, 'Food', 'Cash', '2026-11-01')"
                )
            # Non-positive amount should fail
            with self.assertRaises(Exception):
                cursor.execute(
                    "INSERT INTO transactions (type, amount, category, payment_method, date) VALUES ('expense', -50, 'Food', 'Cash', '2026-11-01')"
                )


if __name__ == "__main__":
    unittest.main()

