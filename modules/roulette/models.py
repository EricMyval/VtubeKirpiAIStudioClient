from dataclasses import dataclass


@dataclass
class RouletteSettings:
    base_amount: int = 200
    increment_per_spin: int = 0


@dataclass
class RouletteItem:
    id: int | None
    title: str
    weight: int
    payload: str
