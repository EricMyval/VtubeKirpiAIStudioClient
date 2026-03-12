import requests
from modules.cabinet.service import get_api_key
from modules.utils.constant import API_BASE

def set_active_donate(event_id: int):
    api_key = get_api_key()
    try:
        requests.post(
            f"{API_BASE}/api/client/widgets/donate-panel/active",
            json={"event_id": event_id},
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": api_key
            },
            timeout=5
        )
    except Exception as e:
        print(f"[DonatePanel] set_active error: {e}")


def clear_active_donate():
    api_key = get_api_key()
    try:
        requests.post(
            f"{API_BASE}/api/client/widgets/donate-panel/active/clear",
            headers={
                "X-API-KEY": api_key
            },
            timeout=5
        )
    except Exception as e:
        print(f"[DonatePanel] clear_active error: {e}")