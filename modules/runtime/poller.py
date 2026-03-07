import requests
import time

from modules.cabinet.service import get_api_key
from modules.donate_panel.donate_panel_service import donate_panel_service

from modules.utils.constant import (
    POLL_INTERVAL,
    API_URL,
    PLATFORM_TYPE_DONATTY,
    PLATFORM_TYPE_DONATTY_AI,
    PLATFORM_TYPE_DONATION_ALERTS,
    PLATFORM_TYPE_DONATION_ALERTS_AI,
    PLATFORM_TYPE_TWITCH_VOICE,
    PLATFORM_TYPE_TWITCH_AI,
    PLATFORM_TYPE_TWITCH_POINTS
)

from modules.utils.ws_client import send_ws_command


class ClientPoller:

    def __init__(self, queue, worker):
        self.queue = queue
        self.worker = worker

    # ======================================

    def start(self):

        while True:

            try:

                # ======================================
                # QUEUE BACKPRESSURE
                # ======================================

                queue_size = self.queue.size()

                if queue_size > 1:
                    time.sleep(0.5)
                    continue

                api_key = get_api_key()

                if not api_key:
                    print("[Poller] API ключ не задан")
                    time.sleep(POLL_INTERVAL)
                    continue

                response = requests.post(
                    API_URL,
                    headers={"X-API-KEY": api_key},
                    timeout=60
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

                    platform = event.get("platform")
                    ws_commands = event.get("ws_commands") or []
                    message = event.get("message")
                    image_url = event.get("image_url")

                    add_to_panel = False

                    # обычные донаты
                    if platform in {
                        PLATFORM_TYPE_DONATTY,
                        PLATFORM_TYPE_DONATTY_AI,
                        PLATFORM_TYPE_DONATION_ALERTS,
                        PLATFORM_TYPE_DONATION_ALERTS_AI,
                        PLATFORM_TYPE_TWITCH_VOICE,
                        PLATFORM_TYPE_TWITCH_AI
                    }:
                        add_to_panel = True

                    # twitch channel points
                    elif platform == PLATFORM_TYPE_TWITCH_POINTS and message:
                        add_to_panel = True

                    if add_to_panel:
                        donate_panel_service.add_event_from_poller(event)

                    # ======================================
                    # IMAGE EVENTS → только панель
                    # ======================================

                    if image_url:
                        continue

                    # ==============================
                    # Twitch Points fallback
                    # ==============================
                    if platform == PLATFORM_TYPE_TWITCH_POINTS and not ws_commands:
                        reward = event.get("reward")
                        if reward:
                            send_ws_command(reward, ws_address)
                        return

                    # ==============================
                    # Standard queue
                    # ==============================
                    self.queue.add_event(event)

            except Exception as e:
                print(f"[Poller] error: {e}")

            time.sleep(POLL_INTERVAL)