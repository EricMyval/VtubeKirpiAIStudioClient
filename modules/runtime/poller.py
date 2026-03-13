import requests
import time
from modules.cabinet.service import get_api_key
from modules.runtime.incoming_event_queue import incomingEventQueue
from modules.utils.constant import POLL_INTERVAL, CLIENT_POLL, LAST_EVENT_URL, PLATFORM_TYPE_TWITCH_POINTS
from modules.utils.ws_client import send_ws_command


class ClientPoller:

    def __init__(self, worker):
        self.worker = worker
        self.last_event_id = self._load_state()

    # ======================================
    # STATE STORAGE
    # ======================================

    def _load_state(self):
        try:
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
                timeout=60
            )
            if response.status_code != 200:
                print(f"[Poller] failed to get last event id: {response.status_code}")
                return 0
            data = response.json()
            last_event_id = int(data.get("last_event_id", 0) + 1)
            print(f"[Poller] synced last_event_id={last_event_id}")
            self.last_event_id = last_event_id
            return last_event_id
        except Exception as e:
            print(f"[Poller] state load error: {e}")
            return 0

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
                    CLIENT_POLL,
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
                # PAUSED
                # ======================================

                self.worker.set_paused(data.get("paused"))

                # ======================================
                # WS ADDRESS
                # ======================================

                ws_address = data.get("ws_address")
                self.worker.set_ws_address(ws_address)

                # ======================================
                # EVENTS
                # ======================================

                events = data.get("events") or []
                for event in events:
                    platform = event.get("platform")
                    ws_commands = event.get("ws_commands") or []
                    if platform == PLATFORM_TYPE_TWITCH_POINTS and ws_commands:
                        reward = event.get("reward")
                        if reward and ws_address:
                            send_ws_command(reward, ws_address)
                    else:
                        incomingEventQueue.add_event(event)

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