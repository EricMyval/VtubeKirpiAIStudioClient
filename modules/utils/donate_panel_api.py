import requests
from modules.cabinet.service import get_api_key
from modules.utils.constant import DONATE_PANEL_ACTIVE_SET, DONATE_PANEL_ACTIVE_CLEAR

def _headers():
    return {
        "Content-Type": "application/json",
        "X-API-KEY": get_api_key()
    }

def set_active_donate(event_id: int):
    try:
        requests.post(
            DONATE_PANEL_ACTIVE_SET,
            json={"event_id": event_id},
            headers=_headers(),
            timeout=10
        )
    except Exception as e:
        print(f"[DonatePanel] set_active error: {e}")


def clear_active_donate():
    try:
        requests.post(
            DONATE_PANEL_ACTIVE_CLEAR,
            headers=_headers(),
            timeout=10
        )
    except Exception as e:
        print(f"[DonatePanel] clear_active error: {e}")