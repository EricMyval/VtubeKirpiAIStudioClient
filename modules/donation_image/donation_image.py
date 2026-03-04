# modules/donation_image/donation_image.py
from modules.web_sockets.sender import send_ws_command
import json
from pathlib import Path

WEB_ADMIN_CONFIG_PATH = Path("web_admin_config.json")

# Кеш адреса (загрузится один раз при первом обращении)
_web_admin_base_url: str | None = None
def _load_web_admin_base_url() -> str:
    """
    Читает web_admin_config.json и возвращает base_url вида:
    http://127.0.0.1:27027
    """
    global _web_admin_base_url
    if _web_admin_base_url is not None:
        return _web_admin_base_url

    host = "127.0.0.1"
    port = 27027

    try:
        data = json.loads(WEB_ADMIN_CONFIG_PATH.read_text(encoding="utf-8"))
        host = str(data.get("host", host)).strip() or host
        port = int(data.get("port", port))
    except Exception as e:
        # Если файла нет/битый — просто используем дефолт и не падаем
        print(f"[web_admin_config] Не удалось прочитать {WEB_ADMIN_CONFIG_PATH}: {e}. Использую {host}:{port}")

    _web_admin_base_url = f"http://{host}:{port}"
    return _web_admin_base_url


def message_with_image(message: str) -> bool:
    return "!image_from_ai:" in (message or "")


def message_get_image_token(message: str) -> str:
    """
    Теперь token = donation_id (строкой).
    """
    if message_with_image(message):
        return (message.split("!image_from_ai:", 1)[1] or "").strip()
    return ""


def show_message_image(message: str, amount: int):
    """
    amount == 90 -> kirpi
    amount == 89 -> taka

    Раньше было: /static/<filename>
    Теперь: /donation-image/<donation_id>
    """
    if not message_with_image(message):
        return

    token = message_get_image_token(message)
    if not token:
        return

    voice_row = None
    voice_id = voice_row["voice_id"] if voice_row else None

    base_url = _load_web_admin_base_url()
    url = f"{base_url}/donation-image/{token}"

    send_ws_command(f'{{"action":"donate_image_id_{voice_id}","data":"{url}"}}')
