import os

MEDIA_HTTP_PREFIX = "/alerts/media/"


class ClientAlertService:

    # =========================================================
    # Нормализация пути медиа / звука
    # =========================================================
    @staticmethod
    def _normalize_media_path(path: str | None) -> str | None:
        if not path:
            return None

        path = str(path).strip()

        # Уже абсолютный URL
        if path.startswith("http://") or path.startswith("https://"):
            return path

        # Уже корректный путь
        if path.startswith(MEDIA_HTTP_PREFIX):
            return path

        # Если пришёл полный файловый путь
        filename = os.path.basename(path)

        return MEDIA_HTTP_PREFIX + filename

    # =========================================================
    # Основная сборка payload
    # =========================================================
    def build_payload(self, event: dict) -> dict | None:
        alert = event.get("alert")
        if not alert:
            return None
        title = alert.get("title", "")
        message = alert.get("message", "")
        media_path = self._normalize_media_path(
            alert.get("media_path")
        )
        sound_raw = alert.get("sound_path") or alert.get("sound")
        sound_path = self._normalize_media_path(sound_raw)
        style = alert.get("style") or {}
        payload = {
            "title": title,
            "message": message if alert.get("show_message", True) else "",
            "media": {
                "path": media_path,
                "type": alert.get("media_type"),
                "position": alert.get("media_position", "top")
            } if media_path else None,
            "sound": sound_path,
            "style": {
                "title": style.get("title") or {},
                "message": style.get("message") or {}
            }
        }

        return payload


alert_service = ClientAlertService()