import json
import re
import random
from pathlib import Path

# ==========================
# Константы типов
# ==========================

DONATION_VOICE = "donation_voice"
DONATION_AI = "donation_ai"
POINTS_VOICE = "points_voice"
POINTS_AI = "points_ai"

MESSAGE_FROM_AI = -1
MESSAGE_FROM_VOICE = 0
MESSAGE_FROM_AI_TWITCH_POINTS = -4
MESSAGE_FROM_VOICE_TWITCH_POINTS = -2
MESSAGE_FROM_AWARD_TWITCH_POINTS = -3

PHRASES_PATH = Path("data/db/phrases.json")

# ==========================
# Дефолтные фразы
# ==========================

DEFAULT_PHRASES = {
    DONATION_VOICE: [
        {
            "before": "{message}",
            "after": "И да, {user}, спасибо за {amount_words} {rubles_form}!"
        }
    ],
    DONATION_AI: [
        {
            "before": "{user} мне пишет: {message}",
            "after": "Спасибо {user} за {amount} рублей!"
        }
    ],
    POINTS_VOICE: [
        {
            "before": "{user} тебе пишет: {message}",
            "after": ""
        }
    ],
    POINTS_AI: [
        {
            "before": "{user} мне пишет: {message}",
            "after": ""
        }
    ]
}

# ==========================
# Менеджер фраз
# ==========================

class PhrasesManager:
    def __init__(self):
        self._ensure()
        self._load()

    def _ensure(self):
        PHRASES_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not PHRASES_PATH.exists():
            PHRASES_PATH.write_text(
                json.dumps(DEFAULT_PHRASES, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

    def _load(self):
        self.data = json.loads(PHRASES_PATH.read_text(encoding="utf-8"))

    def get_random(self, phrase_type: str) -> dict:
        variants = self.data.get(phrase_type, [])
        if not variants:
            return {"before": "{message}", "after": ""}
        return random.choice(variants)


phrases_manager = PhrasesManager()

# ==========================
# Сборка фразы
# ==========================

def build_phrase(phrase_type: str, context: dict) -> str:
    tpl = phrases_manager.get_random(phrase_type)

    before = tpl.get("before", "").format(**context).strip()
    after = tpl.get("after", "").format(**context).strip()

    if before and before[-1] not in ".!?":
        before += "."

    if after:
        return f"{before} {after}".strip()

    return before

# ==========================
# Очистка сообщения
# ==========================

def def_message(message: str) -> str:
    url_pattern = re.compile(
        r'(?:https?://[^\s]+|www\.[^\s]+)',
        re.IGNORECASE
    )

    # Удаляем ссылки
    cleaned = url_pattern.sub(' ', message)

    # Нормализуем пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


# ==========================
# Склонения
# ==========================

def get_rubles_form(amount: int) -> str:
    last_two = amount % 100
    last_one = amount % 10
    if 11 <= last_two <= 19:
        return "рублей"
    if last_one == 1:
        return "рубль"
    if 2 <= last_one <= 4:
        return "рубля"
    return "рублей"

def format_command_template(command: str, amount: int, user: str = "", message: str = "") -> str:
    if not command:
        return command
    replacements = {
        '{amount}': str(amount),
        '{user}': user or '',
        '{message}': message or ''
    }
    formatted_command = command
    for pattern, replacement in replacements.items():
        formatted_command = formatted_command.replace(pattern, replacement)
    return formatted_command

# ==========================
# Удаление команды картинки
# ==========================

def message_non_commands(message: str) -> str:
    message = re.sub(r'!image_from_ai:\d+\.', '', message)
    message = re.sub(r'\s{2,}', ' ', message)
    return message.strip()