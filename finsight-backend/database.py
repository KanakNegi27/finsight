"""SQLite persistence layer for FinSight.

Uses only the Python standard library so no extra dependencies are
required. The database file lives next to this module by default and can
be overridden with the FINSIGHT_DB_PATH environment variable (handy for
tests).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "finsight.db"


def db_path() -> Path:
    return Path(os.environ.get("FINSIGHT_DB_PATH", str(DEFAULT_DB_PATH)))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create the required tables if they do not already exist."""

    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                salt          TEXT    NOT NULL,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS profiles (
                user_id                INTEGER PRIMARY KEY,
                savings                REAL,
                monthly_income         REAL,
                monthly_expenses       REAL,
                monthly_debt_payments  REAL,
                purchase_amount        REAL,
                emergency_reserve      REAL,
                updated_at             TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                name          TEXT    NOT NULL,
                category      TEXT    NOT NULL DEFAULT 'Other',
                amount        REAL    NOT NULL,
                days_from_now INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """
        )


def create_user(
    name: str,
    email: str,
    password_hash: str,
    salt: str,
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, salt)
            VALUES (?, ?, ?, ?)
            """,
            (name, email.lower().strip(), password_hash, salt),
        )
        user_id = cursor.lastrowid

    return get_user_by_id(user_id)


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()

    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


def save_profile(user_id: int, profile: dict) -> dict:
    fields = [
        "savings",
        "monthly_income",
        "monthly_expenses",
        "monthly_debt_payments",
        "purchase_amount",
        "emergency_reserve",
    ]

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO profiles (
                user_id, savings, monthly_income, monthly_expenses,
                monthly_debt_payments, purchase_amount, emergency_reserve,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                savings = excluded.savings,
                monthly_income = excluded.monthly_income,
                monthly_expenses = excluded.monthly_expenses,
                monthly_debt_payments = excluded.monthly_debt_payments,
                purchase_amount = excluded.purchase_amount,
                emergency_reserve = excluded.emergency_reserve,
                updated_at = datetime('now')
            """,
            (
                user_id,
                *[profile.get(field) for field in fields],
            ),
        )

    return get_profile(user_id)


def get_profile(user_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


def add_purchase(
    user_id: int,
    name: str,
    category: str,
    amount: float,
    days_from_now: int,
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO purchases (
                user_id, name, category, amount, days_from_now
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, category, amount, days_from_now),
        )
        purchase_id = cursor.lastrowid

    return get_purchase(purchase_id)


def get_purchase(purchase_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE id = ?",
            (purchase_id,),
        ).fetchone()

    return dict(row) if row else None


def list_purchases(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM purchases
            WHERE user_id = ?
            ORDER BY days_from_now ASC, id ASC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def delete_purchase(user_id: int, purchase_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM purchases WHERE id = ? AND user_id = ?",
            (purchase_id, user_id),
        )

    return cursor.rowcount > 0
