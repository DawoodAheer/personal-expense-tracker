"""
Unit tests for Report generation, monthly comparisons, CSV export, and PDF generation.
"""

import os
import tempfile
import unittest
from database.db import init_db
from services.transaction_service import add_transaction
from services.budget_service import set_budget, get_budget_status
from services.report_service import get_monthly_summary, get_monthly_comparison, get_previous_month
from services.export_service import export_transactions_to_csv, generate_monthly_pdf_report
from services.transaction_service import get_all_transactions


class TestReportService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_reports.db")
        init_db(self.db_path)

        # Populate two months of test data
        # October 2026
        add_transaction("income", 4000.0, "Salary", "Bank Transfer", "2026-10-01", db_path=self.db_path)
        add_transaction("expense", 800.0, "Rent & Housing", "Bank Transfer", "2026-10-02", db_path=self.db_path)
        add_transaction("expense", 200.0, "Groceries", "Debit Card", "2026-10-15", db_path=self.db_path)

        # November 2026
        add_transaction("income", 4500.0, "Salary", "Bank Transfer", "2026-11-01", db_path=self.db_path)
        add_transaction("expense", 800.0, "Rent & Housing", "Bank Transfer", "2026-11-02", db_path=self.db_path)
        add_transaction("expense", 350.0, "Groceries", "Debit Card", "2026-11-05", db_path=self.db_path)
        add_transaction("expense", 150.0, "Utilities & Bills", "Credit Card", "2026-11-10", db_path=self.db_path)

        set_budget("2026-11", "Rent & Housing", 800.0, db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_previous_month_calculation(self):
        self.assertEqual(get_previous_month("2026-11"), "2026-10")
        self.assertEqual(get_previous_month("2026-01"), "2025-12")

    def test_monthly_summary(self):
        summary = get_monthly_summary("2026-11", db_path=self.db_path)
        self.assertEqual(summary["income"], 4500.0)
        self.assertEqual(summary["expense"], 1300.0)
        self.assertEqual(summary["net_savings"], 3200.0)
        self.assertEqual(summary["income_count"], 1)
        self.assertEqual(summary["expense_count"], 3)
        self.assertEqual(summary["top_category"], "Rent & Housing")

    def test_monthly_comparison(self):
        comp = get_monthly_comparison("2026-11", db_path=self.db_path)
        self.assertEqual(comp["current_month"], "2026-11")
        self.assertEqual(comp["previous_month"], "2026-10")
        # Income rose from 4000 to 4500 (+500)
        self.assertEqual(comp["income_delta"], 500.0)
        self.assertEqual(comp["income_pct_delta"], 12.5)
        # Expense rose from 1000 to 1300 (+300)
        self.assertEqual(comp["expense_delta"], 300.0)

    def test_csv_export(self):
        df = get_all_transactions(db_path=self.db_path)
        csv_bytes = export_transactions_to_csv(df)
        self.assertTrue(len(csv_bytes) > 0)
        csv_str = csv_bytes.decode("utf-8")
        self.assertIn("Rent & Housing", csv_str)
        self.assertIn("Salary", csv_str)

    def test_pdf_report_generation(self):
        summary = get_monthly_summary("2026-11", db_path=self.db_path)
        budgets = get_budget_status("2026-11", db_path=self.db_path)
        df = get_all_transactions(month="2026-11", db_path=self.db_path)
        tx_list = df.to_dict(orient="records")

        pdf_bytes = generate_monthly_pdf_report(
            month="2026-11",
            summary=summary,
            transactions=tx_list,
            budgets=budgets,
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000)
        # PDF starts with %PDF
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()

