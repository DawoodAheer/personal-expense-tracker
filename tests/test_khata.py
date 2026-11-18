"""
Unit tests for Smart Khata & Notes parser and database persistence.
Validates natural language hisaab calculations, plus/minus parsing, and note archiving.
"""

import os
import tempfile
import unittest
from database.db import init_db
from services.khata_service import (
    parse_hisaab_text,
    save_khata_note,
    get_khata_note,
    get_all_khata_notes,
    update_khata_note,
    delete_khata_note,
)


class TestKhataService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_khata.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_user_example_1_simple_addition(self):
        """Test: '200 Chicken + 500 Cash = 700'"""
        calc = parse_hisaab_text("200 Chicken + 500 Cash = 700")
        self.assertEqual(calc["item_count"], 2)
        self.assertEqual(calc["total_additions"], 700.0)
        self.assertEqual(calc["total_deductions"], 0.0)
        self.assertEqual(calc["net_total"], 700.0)
        self.assertEqual(calc["items"][0]["amount"], 200.0)
        self.assertEqual(calc["items"][0]["label"], "Chicken")
        self.assertEqual(calc["items"][1]["amount"], 500.0)
        self.assertEqual(calc["items"][1]["label"], "Cash")

    def test_user_example_2_addition_and_subtraction(self):
        """Test: '200 Chicken + 300 Cash + 400 daal - 100 - 20 aloo Sabzii' -> 780"""
        calc = parse_hisaab_text("200 Chicken + 300 Cash + 400 daal - 100 - 20 aloo Sabzii")
        self.assertEqual(calc["item_count"], 5)
        # Additions: 200 + 300 + 400 = 900
        self.assertEqual(calc["total_additions"], 900.0)
        # Deductions: 100 + 20 = 120
        self.assertEqual(calc["total_deductions"], 120.0)
        # Net: 900 - 120 = 780
        self.assertEqual(calc["net_total"], 780.0)

    def test_multiline_hisaab_notes(self):
        """Test multi-line format with mixed positive and negative lines."""
        text = """
        50000 Salary
        + 1500 Freelance
        - 12000 House Rent
        - 3500 Electricity Bill
        """
        calc = parse_hisaab_text(text)
        self.assertEqual(calc["item_count"], 4)
        self.assertEqual(calc["total_additions"], 51500.0)
        self.assertEqual(calc["total_deductions"], 15500.0)
        self.assertEqual(calc["net_total"], 36000.0)

    def test_save_and_retrieve_note(self):
        """Ensure notes are permanently saved and never lost in SQLite."""
        note = save_khata_note(
            title="Kitchen Hisaab",
            raw_text="200 Chicken + 300 Cash + 400 daal - 100 - 20 aloo Sabzii",
            date_str="2026-11-19",
            db_path=self.db_path,
        )
        self.assertIsNotNone(note["id"])
        self.assertEqual(note["title"], "Kitchen Hisaab")
        self.assertEqual(note["calculated_total"], 780.0)
        self.assertEqual(note["month"], "2026-11")

        fetched = get_khata_note(note["id"], db_path=self.db_path)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched["title"], "Kitchen Hisaab")
        self.assertEqual(len(fetched["items"]), 5)

    def test_filter_and_search_notes(self):
        save_khata_note("Rashan Nov", "1000 flour + 500 oil", "2026-11-01", db_path=self.db_path)
        save_khata_note("Rashan Dec", "1200 flour + 600 oil", "2026-12-01", db_path=self.db_path)

        # By month
        nov_notes = get_all_khata_notes(month="2026-11", db_path=self.db_path)
        self.assertEqual(len(nov_notes), 1)
        self.assertEqual(nov_notes[0]["title"], "Rashan Nov")

        # By keyword search
        search_res = get_all_khata_notes(search_query="Dec", db_path=self.db_path)
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]["title"], "Rashan Dec")

    def test_update_and_delete_note(self):
        note = save_khata_note("Test Note", "100 A + 200 B", "2026-11-19", db_path=self.db_path)
        self.assertEqual(note["calculated_total"], 300.0)

        # Update note
        ok = update_khata_note(note["id"], "Updated Note", "100 A + 500 B", "2026-11-19", db_path=self.db_path)
        self.assertTrue(ok)
        updated = get_khata_note(note["id"], db_path=self.db_path)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["calculated_total"], 600.0)

        # Delete note
        delete_khata_note(note["id"], db_path=self.db_path)
        self.assertIsNone(get_khata_note(note["id"], db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()

