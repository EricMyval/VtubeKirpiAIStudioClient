from typing import List, Optional
from datetime import datetime

from .db import get_connection
from .models import Donate
from .session_stats import donation_session_stats


class DonateRepository:

    # ==========================================================
    # ADD DONATE
    # ==========================================================

    @staticmethod
    def add(
        platform: str,
        username: str,
        amount: int,
        message: str,
        extra: Optional[str] = None,
    ) -> int:
        conn = get_connection()
        cursor = conn.cursor()

        created_at = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO donations
            (platform, username, amount, message, created_at, extra)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                platform,
                username,
                amount,
                message,
                created_at,
                extra,
            ),
        )

        conn.commit()

        donate_id = cursor.lastrowid
        conn.close()

        return donate_id

    # ==========================================================
    # GET BY ID
    # ==========================================================

    @staticmethod
    def get_by_id(donate_id: int) -> Optional[Donate]:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM donations
            WHERE id = ?
            """,
            (donate_id,),
        )

        row = cursor.fetchone()
        conn.close()

        return Donate.from_row(row)

    # ==========================================================
    # FIND LAST (для mark_playing)
    # ==========================================================

    @staticmethod
    def find_last(username: str, amount: int) -> Optional[Donate]:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM donations
            WHERE username = ?
            AND amount = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (username, amount),
        )

        row = cursor.fetchone()
        conn.close()

        return Donate.from_row(row)

    # ==========================================================
    # HISTORY
    # ==========================================================

    @staticmethod
    def get_all(limit: Optional[int] = None) -> List[Donate]:

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT *
            FROM donations
            ORDER BY id DESC
        """

        if limit:
            sql += " LIMIT ?"
            cursor.execute(sql, (limit,))
        else:
            cursor.execute(sql)

        rows = cursor.fetchall()
        conn.close()

        return [Donate.from_row(row) for row in rows]

    # ==========================================================
    # UPDATE STATUS
    # ==========================================================

    @staticmethod
    def update_status(donate_id: int, status: str):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE donations
            SET status = ?
            WHERE id = ?
            """,
            (status, donate_id),
        )

        conn.commit()
        conn.close()

    # ==========================================================
    # REPEAT
    # ==========================================================

    @staticmethod
    def repeat(donate_id: int) -> bool:

        donate = DonateRepository.get_by_id(donate_id)

        if not donate:
            return False

        DonateRepository.add(
            platform=donate.platform,
            username=donate.username,
            amount=donate.amount,
            message=donate.message,
            extra="repeat",
        )

        return True