import os
import shutil
from pathlib import Path

from modules.utils.runtime_paths import app_root

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
    # Копирование медиа если его нет локально
    # =========================================================
    @staticmethod
    def _ensure_local_media(path: str | None) -> str | None:
        if not path:
            return None

        src = Path(path)

        # если файл не существует — ничего не делаем
        if not src.exists():
            return path

        alerts_media_dir = app_root() / "data" / "alerts_media"
        alerts_media_dir.mkdir(parents=True, exist_ok=True)

        dst = alerts_media_dir / src.name

        if not dst.exists():
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"[ALERT MEDIA] copy failed: {src} -> {dst} ({e})")
                return path

        return str(dst)

    # =========================================================
    # Основная сборка payload
    # =========================================================
    def build_payload(self, event: dict) -> dict | None:
        alert = event.get("alert")
        if not alert:
            return None

        # =====================================================
        # Копируем медиа если нужно
        # =====================================================

        media_src = alert.get("media_path")
        sound_src = alert.get("sound_path") or alert.get("sound")

        alert["media_path"] = self._ensure_local_media(media_src)
        alert["sound_path"] = self._ensure_local_media(sound_src)

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