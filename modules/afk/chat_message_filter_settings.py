import json
from pathlib import Path


class ChatMessageFilterSettings:
    DEFAULTS = {
        "recent_unique_messages": 20,
        "similarity_threshold": 0.85,
        "min_unique_word_ratio": 0.4,
        "min_message_length": 3,
        "spam_phrases": [
            "{user}, попрошу не спамить, на такое я отвечать не хочу"
        ],
        "repeat_phrases": [
            "{user}, на это я уже отвечал, лучше спроси что-то новое и интересное"
        ]
    }

    def __init__(self, path: str = "data/db/chat_message_filter_settings.json"):
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

    # ========= API =========

    def get_all(self) -> dict:
        return self.data

    def update_from_form(self, data: dict):
        for key in self.DEFAULTS:
            if key not in data:
                continue

            value = data[key]

            if isinstance(self.DEFAULTS[key], int):
                self.data[key] = int(value)
            elif isinstance(self.DEFAULTS[key], float):
                self.data[key] = float(value)
            elif isinstance(self.DEFAULTS[key], list):
                self.data[key] = [
                    v.strip() for v in value.splitlines() if v.strip()
                ]

        self._save()

chat_message_filter_settings = ChatMessageFilterSettings()