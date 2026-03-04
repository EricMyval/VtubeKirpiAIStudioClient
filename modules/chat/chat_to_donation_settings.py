import json
from pathlib import Path


class ChatToDonationControllerSettings:
    DEFAULTS = {
        "max_queue": 5,
        "afk_intro_text": (
            "Наш пушистый енотик Эрик отошел по своим важным енотьим делам, "
            "а пока его нет, с вами посижу я, Кирпи. "
            "Буду отвечать на сообщения в чатике, а также разбирать ваши донатики. "
            "Давайте весело проведем время!"
        )
    }

    def __init__(self, path: str = "data/db/ChatToDonationControllerSettings.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            self.data = self.DEFAULTS.copy()
            self._save()
            return

        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self.data = self.DEFAULTS.copy()
            self._save()

        changed = False
        for key, value in self.DEFAULTS.items():
            if key not in self.data:
                self.data[key] = value
                changed = True

        if changed:
            self._save()

    def _save(self):
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ========= getters =========

    @property
    def max_queue(self) -> int:
        return int(self.data.get("max_queue", self.DEFAULTS["max_queue"]))

    @property
    def afk_intro_text(self) -> str:
        return str(self.data.get(
            "afk_intro_text",
            self.DEFAULTS["afk_intro_text"]
        ))

    # ========= setters =========

    def set_max_queue(self, value: int):
        self.data["max_queue"] = max(1, min(int(value), 50))
        self._save()

    def set_afk_intro_text(self, text: str):
        text = (text or "").strip()
        if not text:
            text = self.DEFAULTS["afk_intro_text"]

        self.data["afk_intro_text"] = text
        self._save()

    # ========= web =========

    def update_from_form(self, data: dict):
        if "max_queue" in data:
            try:
                self.set_max_queue(data["max_queue"])
            except Exception:
                pass

        if "afk_intro_text" in data:
            self.set_afk_intro_text(data["afk_intro_text"])
