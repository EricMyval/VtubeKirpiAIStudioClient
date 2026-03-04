import random
from typing import Callable, Optional

from modules.client.roulette.config_repo import RouletteConfigRepository
from modules.client.roulette.models import RouletteItem


class RouletteSpinResult:

    def __init__(self, item: RouletteItem, spin_index: int, price: int):
        self.item = item
        self.spin_index = spin_index
        self.price = price


class RouletteEngine:
    """
    Один engine = одна сессия накопления денег.
    """

    def __init__(
        self,
        repo: RouletteConfigRepository,
        on_spin: Optional[Callable[[RouletteSpinResult], None]] = None
    ):
        self.repo = repo
        self.on_spin = on_spin

        self._buffer = 0

    # --------------------------

    def spin_once_force(self):
        """
        Принудительная прокрутка (для теста).
        Без учёта суммы.
        """

        items = self.repo.get_items()
        if not items:
            return None

        item = self._pick_weighted_item(items)

        return item, items


    def push_amount(self, amount: int) -> list[RouletteSpinResult]:
        """
        Принимаем сумму.
        Возвращаем список совершённых круток.
        """

        if amount <= 0:
            return []

        self._buffer += amount

        settings = self.repo.get_settings()
        items = self.repo.get_items()

        if not items:
            return []

        results: list[RouletteSpinResult] = []

        spin_index = 0

        while True:
            price = settings.base_amount + spin_index * settings.increment_per_spin

            if price <= 0:
                break

            if self._buffer < price:
                break

            self._buffer -= price

            item = self._pick_weighted_item(items)

            result = RouletteSpinResult(
                item=item,
                spin_index=spin_index,
                price=price
            )

            results.append(result)

            if self.on_spin:
                self.on_spin(result)

            spin_index += 1

        return results

    # --------------------------

    def reset_buffer(self):
        self._buffer = 0

    def get_buffer(self) -> int:
        return self._buffer

    # --------------------------

    def _pick_weighted_item(self, items: list[RouletteItem]) -> RouletteItem:
        """
        Выбор по весам.
        """

        total = sum(max(0, i.weight) for i in items)

        # если все веса вдруг нулевые
        if total <= 0:
            return random.choice(items)

        r = random.uniform(0, total)
        upto = 0.0

        for item in items:
            w = max(0, item.weight)
            upto += w
            if r <= upto:
                return item

        return items[-1]
