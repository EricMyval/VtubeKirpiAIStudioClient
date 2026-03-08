import requests
from modules.cabinet.service import get_api_key
from modules.utils.constant import WIDGETS_URL


class ClientConfigLoader:

    @staticmethod
    def _get(endpoint: str) -> dict:
        api_key = get_api_key()

        if not api_key:
            raise RuntimeError("API ключ клиента не задан. Укажите его в личном кабинете.")

        try:
            response = requests.get(
                f"{WIDGETS_URL}/{endpoint}",
                headers={"X-API-KEY": api_key},
                timeout=15
            )

            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            if response.status_code == 401:
                raise RuntimeError("Неверный API ключ клиента")
            raise RuntimeError(f"Ошибка загрузки конфига {endpoint}: {e}")

        except Exception as e:
            raise RuntimeError(
                f"Не удалось загрузить конфиг {endpoint} с сервера: {e}"
            )

    # ---------------- TTS ----------------

    @staticmethod
    def load_tts_config() -> dict:
        return ClientConfigLoader._get("tts")