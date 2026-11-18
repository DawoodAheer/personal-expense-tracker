"""
Unit tests for Financial Goals service.
Tests goal creation, savings progress tracking, contributions, and completion status.
"""

import os
import tempfile
import unittest
from database.db import init_db
from services.goals_service import (
    add_goal,
    get_goal,
    get_all_goals,
    update_goal_savings,
    add_to_goal_savings,
    delete_goal,
    reset_goal,
)


class TestGoalsService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_goals.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_get_goal(self):
        goal = add_goal(
            name="Emergency Fund",
            target_amount=10000.0,
            category="Emergency Fund",
            deadline="2027-12-31",
            description="Safety net",
            db_path=self.db_path,
        )
        self.assertIsNotNone(goal["id"])
        self.assertEqual(goal["name"], "Emergency Fund")
        self.assertEqual(goal["target_amount"], 10000.0)
        self.assertEqual(goal["saved_amount"], 0.0)
        self.assertEqual(goal["status"], "IN_PROGRESS")
        self.assertEqual(goal["percentage"], 0.0)

        fetched = get_goal(goal["id"], db_path=self.db_path)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched["name"], "Emergency Fund")

    def test_add_to_goal_savings(self):
        goal = add_goal(
            name="Laptop",
            target_amount=1000.0,
            category="Electronics / Gadgets",
            db_path=self.db_path,
        )
        # Add 400
        ok = add_to_goal_savings(goal["id"], 400.0, db_path=self.db_path)
        self.assertTrue(ok)

        updated = get_goal(goal["id"], db_path=self.db_path)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["saved_amount"], 400.0)
        self.assertEqual(updated["remaining"], 600.0)
        self.assertEqual(updated["percentage"], 40.0)
        self.assertEqual(updated["status"], "IN_PROGRESS")

        # Add 600 more -> reaches 1000 (auto-completed)
        add_to_goal_savings(goal["id"], 600.0, db_path=self.db_path)
        completed = get_goal(goal["id"], db_path=self.db_path)
        self.assertIsNotNone(completed)
        assert completed is not None
        self.assertEqual(completed["saved_amount"], 1000.0)
        self.assertEqual(completed["remaining"], 0.0)
        self.assertEqual(completed["percentage"], 100.0)
        self.assertEqual(completed["status"], "ACHIEVED")

    def test_update_goal_savings_and_reset(self):
        goal = add_goal(
            name="Vacation",
            target_amount=2000.0,
            category="Vacation / Travel",
            db_path=self.db_path,
        )
        update_goal_savings(goal["id"], 2000.0, db_path=self.db_path)
        g = get_goal(goal["id"], db_path=self.db_path)
        self.assertIsNotNone(g)
        assert g is not None
        self.assertEqual(g["status"], "ACHIEVED")

        # Reset back to 0
        reset_goal(goal["id"], db_path=self.db_path)
        reset_g = get_goal(goal["id"], db_path=self.db_path)
        self.assertIsNotNone(reset_g)
        assert reset_g is not None
        self.assertEqual(reset_g["saved_amount"], 0.0)
        self.assertEqual(reset_g["status"], "IN_PROGRESS")

    def test_delete_goal(self):
        goal = add_goal(
            name="Temp Goal",
            target_amount=500.0,
            db_path=self.db_path,
        )
        self.assertEqual(len(get_all_goals(db_path=self.db_path)), 1)
        delete_goal(goal["id"], db_path=self.db_path)
        self.assertEqual(len(get_all_goals(db_path=self.db_path)), 0)

    def test_invalid_goal_inputs(self):
        with self.assertRaises(ValueError):
            add_goal("", 1000.0, db_path=self.db_path)
        with self.assertRaises(ValueError):
            add_goal("Valid Name", -10.0, db_path=self.db_path)


if __name__ == "__main__":
    unittest.main()
