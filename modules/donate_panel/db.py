import sqlite3
import os

DB_PATH = os.path.join("data", "db", "donate_panel.db")


def get_connection():

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")

    return conn


def _column_exists(cursor, table, column):

    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row["name"] for row in cursor.fetchall()]
    return column in cols


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

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            extra TEXT,

            raw_event TEXT,

            status TEXT NOT NULL DEFAULT 'queued'
        )
        """
    )

    # миграция старой базы
    if not _column_exists(cursor, "donations", "raw_event"):
        cursor.execute("ALTER TABLE donations ADD COLUMN raw_event TEXT")

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_donations_status
        ON donations(status)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_donations_created
        ON donations(created_at DESC)
        """
    )

    conn.commit()
    conn.close()


init_db()