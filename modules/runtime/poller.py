import os
import json
import requests
import time

from modules.cabinet.service import get_api_key
from modules.utils.constant import (
    POLL_INTERVAL,
    API_URL,
    LAST_EVENT_URL,
    PLATFORM_TYPE_TWITCH_POINTS
)

from modules.utils.ws_client import send_ws_command


STATE_FILE = "data/db/client_state.json"


class ClientPoller:

    def __init__(self, queue, worker):

        self.queue = queue
        self.worker = worker

        self.last_event_id = self._load_state()

    # ======================================
    # STATE STORAGE
    # ======================================

    def _load_state(self):

        try:

            if os.path.exists(STATE_FILE):

                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}

                return int(data.get("last_event_id", 0))

            print("[Poller] state file not found, requesting last event id")

            api_key = get_api_key()

            if not api_key:
                print("[Poller] API key missing")
                return 0

            response = requests.get(
                LAST_EVENT_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": api_key
                },
                timeout=10
            )

            if response.status_code != 200:
                print(f"[Poller] failed to get last event id: {response.status_code}")
                return 0

            data = response.json()

            last_event_id = int(data.get("last_event_id", 0) + 1)

            print(f"[Poller] synced last_event_id={last_event_id}")

            self.last_event_id = last_event_id
            self._save_state()

            return last_event_id

        except Exception as e:
            print(f"[Poller] state load error: {e}")
            return 0

    # --------------------------------------

    def _save_state(self):

        try:

            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {"last_event_id": self.last_event_id},
                    f,
                    indent=2
                )

        except Exception as e:
            print(f"[Poller] state save error: {e}")

    # ======================================
    # MAIN LOOP
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
                    json={"last_event_id": self.last_event_id},
                    headers={
                        "Content-Type": "application/json",
                        "X-API-KEY": api_key
                    },
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

                    # Twitch Points fallback

                    if platform == PLATFORM_TYPE_TWITCH_POINTS and not ws_commands:

                        reward = event.get("reward")

                        if reward and ws_address:
                            send_ws_command(reward, ws_address)

                        continue

                    self.queue.add_event(event)

                # ======================================
                # LAST EVENT ID
                # ======================================

                new_last_event_id = data.get("last_event_id")

                if new_last_event_id is not None:

                    try:
                        new_last_event_id = int(new_last_event_id)

                        if new_last_event_id != self.last_event_id:
                            self.last_event_id = new_last_event_id
                            self._save_state()

                    except Exception:
                        pass

            except Exception as e:

                print(f"[Poller] error: {e}")

            time.sleep(POLL_INTERVAL)