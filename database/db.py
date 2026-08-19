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
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


def seed_db():
    """Insert sample data for development. Safe to call multiple times."""
    conn = get_db()

    existing = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.dev",)).fetchone()
    if existing is None:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.dev", generate_password_hash("password123")),
        )
        user_id = cursor.lastrowid

        conn.executemany(
            "INSERT INTO expenses (user_id, description, amount, category, date) VALUES (?, ?, ?, ?, ?)",
            [
                (user_id, "Groceries", 54.32, "Food", "2026-08-01"),
                (user_id, "Electric bill", 88.10, "Utilities", "2026-08-05"),
                (user_id, "Movie tickets", 24.00, "Entertainment", "2026-08-12"),
            ],
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Convenience entry point: `python -m database.db` sets up a dev database.
    init_db()
    seed_db()
    print(f"Database ready at {DB_PATH}")
