import requests
import time

from modules.client.cabinet.service import get_api_key
from modules.client.donate_panel.donate_panel_service import donate_panel_service


API_URL = "https://kirpi-gpt.ru/api/client/poll"
POLL_INTERVAL = 2.0


class ClientPoller:

    def __init__(self, queue, worker):

        self.queue = queue
        self.worker = worker

    # ======================================

    def start(self):

        while True:

            try:

                api_key = get_api_key()

                if not api_key:
                    print("[Poller] API ключ не задан")
                    time.sleep(POLL_INTERVAL)
                    continue

                response = requests.post(
                    API_URL,
                    headers={"X-API-KEY": api_key},
                    timeout=10
                )

                if response.status_code == 401:
                    print("[Poller] Неверный API ключ")
                    time.sleep(POLL_INTERVAL)
                    continue

                if response.status_code != 200:
                    print(f"[Poller] HTTP error: {response.status_code}")
                    time.sleep(POLL_INTERVAL)
                    continue

                data = response.json()

                if not data.get("success"):
                    time.sleep(POLL_INTERVAL)
                    continue

                # ======================================
                # WS ADDRESS
                # ======================================

                ws_address = data.get("ws_address")

                if ws_address:
                    self.worker.set_ws_address(ws_address)

                # ======================================
                # EVENTS
                # ======================================

                events = data.get("events") or []

                for event in events:

                    amount = int(event.get("amount", 0) or 0)

                    # добавляем в панель только донаты
                    if amount > 0:
                        donate_panel_service.add_event_from_poller(event)

                    # добавляем событие в очередь worker
                    self.queue.add_event(event)

            except Exception as e:

                print(f"[Poller] error: {e}")

            time.sleep(POLL_INTERVAL)