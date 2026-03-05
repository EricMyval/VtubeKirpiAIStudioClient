import requests

from modules.client.cabinet.service import get_api_key
from modules.utils.constant import WIDGETS_URL
from modules.client.afk.afk_state import afk_state


class AFKService:

    @staticmethod
    def _get(endpoint: str):

        api_key = get_api_key()

        if not api_key:
            raise RuntimeError("API ключ не задан")

        url = f"{WIDGETS_URL}/{endpoint}"

        r = requests.get(
            url,
            headers={"X-API-KEY": api_key},
            timeout=10
        )

        r.raise_for_status()

        data = r.json()

        # синхронизируем локальное состояние
        if "afk_enabled" in data:
            afk_state.set_enabled(data["afk_enabled"])

        return data

    # ============================

    @staticmethod
    def enable():

        return AFKService._get("enable")

    # ============================

    @staticmethod
    def disable():

        return AFKService._get("disable")

    # ============================

    @staticmethod
    def status():

        return AFKService._get("status")