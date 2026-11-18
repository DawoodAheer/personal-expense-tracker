"""
Database initialization and connection management for Personal Expense Tracker.
Uses SQLite for robust, zero-configuration local storage.
"""

import sqlite3
import os
from contextlib import contextmanager

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expense_tracker.db")


def get_db_path():
    """Retrieve database path from environment variable or default."""
    return os.getenv("EXPENSE_TRACKER_DB", DEFAULT_DB_PATH)


@contextmanager
def get_connection(db_path=None):
    """Context manager for SQLite database connection.
    Ensures safe commit on success and rollback on error.
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None):
    """Create tables and indexes if they do not exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(month, category)
            );
        """)

        # Settings table for user preferences (currency, formats, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # Financial Goals table: track savings targets and deadlines
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL CHECK(target_amount > 0),
                saved_amount REAL NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT 'General',
                deadline TEXT,
                description TEXT,
                is_completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Recurring Transactions table: auto-generate monthly/weekly entries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                recurrence TEXT NOT NULL DEFAULT 'monthly',
                next_due_date TEXT NOT NULL,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Smart Khata / Monthly Notes Hisaab table (Text notes with auto-calculated items)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS khata_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                month TEXT NOT NULL,
                date TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                calculated_total REAL NOT NULL,
                breakdown_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Indexes for new tables
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_completed ON goals(is_completed);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_due ON recurring_transactions(next_due_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_active ON recurring_transactions(is_active);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_khata_month ON khata_notes(month);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_khata_date ON khata_notes(date);")

        # Indexes for fast querying & reporting
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_month ON budgets(month);")


def get_setting(key: str, default: str = "", db_path=None) -> str:
    """Retrieve a setting value by key."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return str(row["value"]) if row else default


def set_setting(key: str, value: str, db_path=None) -> None:
    """Save or update a setting value."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def reset_database_to_zero(db_path=None) -> None:
    """Clear all transactions, budgets, goals, recurring, and khata notes so user can start fresh from 0."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions;")
        cursor.execute("DELETE FROM budgets;")
        cursor.execute("DELETE FROM goals;")
        cursor.execute("DELETE FROM recurring_transactions;")
        cursor.execute("DELETE FROM khata_notes;")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('transactions', 'budgets', 'goals', 'recurring_transactions', 'khata_notes');")


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", get_db_path())

