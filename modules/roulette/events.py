from dataclasses import dataclass

from modules.roulette.models import RouletteItem


@dataclass
class RouletteSpinEvent:
    item: RouletteItem
    spin_index: int
    price: int
