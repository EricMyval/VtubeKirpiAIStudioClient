import time
from collections import deque
from typing import Set
from modules.chat.chat_message_filter import chat_message_filter
from modules.donation.donation_monitor import donation_monitor
from modules.phrases.phrases import MESSAGE_FROM_AI_TWITCH_POINTS, MESSAGE_FROM_VOICE
from modules.afk.afk_state import afk_state
from modules.player.donation_runtime import get_queue_stats
from modules.web_admin.shared import chat_to_donation_settings


class ChatToDonationController:
    def __init__(self, buffer_size=20):
        self.chat_buffer = deque(maxlen=buffer_size)
        self.used_message_ids: Set[str] = set()

    @property
    def max_queue(self) -> int:
        # всегда актуальное значение (под веб)
        return chat_to_donation_settings.max_queue

    def on_chat_message(self, payload: dict):
        # ❌ если AFK выключен — чат игнорируем
        if not afk_state.is_enabled():
            return

        msg_id = payload.get("message_id")
        user = payload.get("user") or "Unknown"
        text = (payload.get("text") or "").strip()

        if not msg_id or not text:
            return

        print(f"🟣 CHAT | {user}: {text} (id={msg_id})")

        # 🧠 ФИЛЬТР ЧАТА
        result = chat_message_filter.process(user, text)

        # если спам или повтор — дефолтный ответ, есди "." в response, то не добавляем в очередь
        if result["is_spam"] or result["is_repeat"]:
            if result["response"] != ".":
                donation_monitor.db.add_donate(
                    user,
                    result["response"],
                    str(MESSAGE_FROM_VOICE)
                )
            print(f"🚫 CHAT FILTER | {user}: {result['response']}")
            return

        # ✅ всё ок — сохраняем ОРИГИНАЛ
        self.chat_buffer.append({
            "id": msg_id,
            "user": user,
            "text": text,
            "ts": time.time()
        })

        self._try_push_chat_to_queue()

    def _try_push_chat_to_queue(self):
        stats = get_queue_stats()

        # если очередь уже заполнена — выходим
        if stats["current_queue_size"] >= self.max_queue:
            return

        # ищем самое свежее сообщение, которое ещё не использовали
        for msg in reversed(self.chat_buffer):
            if msg["id"] in self.used_message_ids:
                continue

            donation_monitor.db.add_donate(
                msg["user"],
                msg["text"],
                str(MESSAGE_FROM_AI_TWITCH_POINTS)
            )

            self.used_message_ids.add(msg["id"])
            print(f"💬 CHAT→QUEUE | {msg['user']}: {msg['text']}")
            return
