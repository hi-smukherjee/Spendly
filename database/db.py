# Students will write this file in Step 1 — Database Setup
# This file should contain:
#   get_db()   — returns a SQLite connection with row_factory and foreign keys enabled
#   init_db()  — creates all tables using CREATE TABLE IF NOT EXISTS
#   seed_db()  — inserts sample data for development

import os
import sqlite3

from werkzeug.security import generate_password_hash

# expense_tracker.db lives at the project root (one level up from database/),
# regardless of the working directory the app is launched from.
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expense_tracker.db")


def get_db():
    """Return a SQLite connection with row access by column name and FK enforcement on."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't already exist."""
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users (id),
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            description TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()
    conn.close()


def seed_db():
    """Insert sample data for development. Safe to call multiple times."""
    conn = get_db()

    if conn.execute("SELECT id FROM users LIMIT 1").fetchone() is not None:
        conn.close()
        return

    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cursor.lastrowid

    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 54.32, "Food", "2026-08-01", "Groceries"),
            (user_id, 42.00, "Transport", "2026-08-03", "Gas fill-up"),
            (user_id, 88.10, "Bills", "2026-08-05", "Electric bill"),
            (user_id, 22.50, "Health", "2026-08-07", "Pharmacy pickup"),
            (user_id, 24.00, "Entertainment", "2026-08-10", "Movie tickets"),
            (user_id, 65.99, "Shopping", "2026-08-13", "New shoes"),
            (user_id, 15.75, "Other", "2026-08-16", "Miscellaneous"),
            (user_id, 47.60, "Food", "2026-08-18", "Dinner out"),
        ],
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Convenience entry point: `python -m database.db` sets up a dev database.
    init_db()
    seed_db()
    print(f"Database ready at {DB_PATH}")
