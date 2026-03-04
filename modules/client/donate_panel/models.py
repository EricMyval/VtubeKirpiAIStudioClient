from dataclasses import dataclass
from typing import Optional


@dataclass
class Donate:

    id: Optional[int]

    platform: str
    username: str
    amount: int
    message: str

    created_at: str

    extra: Optional[str] = None

    status: str = "queued"