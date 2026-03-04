from dataclasses import dataclass

from modules.client.roulette.models import RouletteItem


@dataclass
class RouletteSpinEvent:
    item: RouletteItem
    spin_index: int
    price: int
