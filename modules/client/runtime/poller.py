# modules/client/runtime/poller.py

import requests
import time
from modules.client.cabinet.service import get_api_key

API_URL = "https://kirpi-gpt.ru/api/client/poll"
POLL_INTERVAL = 2.0


class ClientPoller:

    def __init__(self, queue, worker):
        self.queue = queue
        self.worker = worker

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

                response.raise_for_status()
                data = response.json()

                if data.get("success"):

                    if data.get("ws_address"):
                        self.worker.set_ws_address(
                            data.get("ws_address")
                        )

                    for event in data.get("events", []):
                        self.queue.add_event(event)

            except Exception as e:
                print(f"[Poller] error: {e}")

            time.sleep(POLL_INTERVAL)