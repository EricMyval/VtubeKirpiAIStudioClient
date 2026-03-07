# modules/roulette/config_repo.py

from .models import RouletteSettings, RouletteItem


class RouletteConfigRepository:

    def __init__(self):
        self._settings = RouletteSettings()
        self._items: list[RouletteItem] = []
        self._enabled: bool = True

    # ---------------- SETTINGS ----------------

    def set_from_api(self, data: dict):

        self._enabled = bool(data.get("enabled", True))

        self._settings = RouletteSettings(
            base_amount=int(data.get("base_amount", 200)),
            increment_per_spin=int(data.get("increment_per_spin", 0))
        )

        self._items = [
            RouletteItem(
                id=item["id"],
                title=item["title"],
                weight=item["weight"],
                payload=item.get("payload", "")
            )
            for item in data.get("items", [])
        ]

    def is_enabled(self) -> bool:
        return self._enabled

    def get_settings(self) -> RouletteSettings:
        return self._settings

    def get_items(self) -> list[RouletteItem]:
        return list(self._items)