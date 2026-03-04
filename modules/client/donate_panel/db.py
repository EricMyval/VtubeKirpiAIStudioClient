import sqlite3
import os

DB_PATH = os.path.join("data", "db", "donate_panel.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            platform TEXT,
            username TEXT NOT NULL,
            amount INTEGER NOT NULL,
            message TEXT,

            created_at TEXT NOT NULL,

            extra TEXT,
            status TEXT NOT NULL DEFAULT 'queued'
            -- queued | playing | played | skipped
        )
        """
    )

    conn.commit()
    conn.close()

init_db()