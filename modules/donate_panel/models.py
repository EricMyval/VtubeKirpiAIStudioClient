from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Donate:

    id: Optional[int]

    platform: str
    username: str
    amount: int
    message: str

    created_at: Optional[str] = None

    extra: Optional[str] = None

    status: str = "queued"

    raw_event: Optional[str] = None

    # ======================================
    # FROM DB ROW
    # ======================================

    @staticmethod
    def from_row(row: sqlite3.Row) -> "Donate":

        if not row:
            return None

        return Donate(
            id=row["id"],
            platform=row["platform"],
            username=row["username"],
            amount=row["amount"],
            message=row["message"],
            created_at=row["created_at"],
            extra=row["extra"],
            status=row["status"],
            raw_event=row["raw_event"] if "raw_event" in row.keys() else None,
        )

    # ======================================
    # TO DICT (для API)
    # ======================================

    def to_dict(self):

        return {
            "id": self.id,
            "platform": self.platform,
            "username": self.username,
            "amount": self.amount,
            "message": self.message,
            "created_at": self.created_at,
            "extra": self.extra,
            "status": self.status,
        }