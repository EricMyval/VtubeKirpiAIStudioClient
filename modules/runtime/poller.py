import requests
import time

from modules.alerts.alert_control import request_stop
from modules.cabinet.service import get_api_key
from modules.runtime.incoming_event_queue import incomingEventQueue
from modules.tts.runtime import tts_runtime
from modules.utils.constant import POLL_INTERVAL, CLIENT_POLL, LAST_EVENT_URL
from modules.utils.ws_client import send_ws_command


class ClientPoller:

    def __init__(self, worker):
        self.worker = worker

        self.session = requests.Session()

        self._ssl_failed = False
        self._no_key_logged = False
        self._state_initialized = False

        self.last_event_id = self._load_state()

    # ======================================
    # SAFE REQUEST
    # ======================================

    def _request(self, method, url, **kwargs):
        try:
            return self.session.request(method, url, **kwargs)

        except requests.exceptions.SSLError:
            if not self._ssl_failed:
                print("[Poller] ⚠️ SSL failed → switching to unsafe mode")
                self._ssl_failed = True

            return self.session.request(method, url, verify=False, **kwargs)

    # ======================================
    # STATE STORAGE
    # ======================================

    def _load_state(self):
        api_key = get_api_key()

        if not api_key:
            print("[Poller] API key missing")
            return 0

        for attempt in range(3):
            try:
                response = self._request(
                    "GET",
                    LAST_EVENT_URL,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-KEY": api_key
                    },
                    timeout=10
                )

                if response.status_code != 200:
                    print(f"[Poller] bad status: {response.status_code}")
                    continue

                data = response.json()
                last_event_id = int(data.get("last_event_id", 0)) + 1

                print(f"[Poller] synced last_event_id={last_event_id}")
                return last_event_id

            except requests.exceptions.RequestException as e:
                print(f"[Poller] request error (attempt {attempt + 1}): {e}")

        print("[Poller] fallback → using 0")
        return 0

    # ======================================
    # MAIN LOOP
    # ======================================

    def start(self):
        while True:
            try:
                api_key = get_api_key()

                # ---------------- API KEY ----------------

                if not api_key:
                    if not self._no_key_logged:
                        print("[Poller] API ключ не задан")
                        self._no_key_logged = True

                    time.sleep(POLL_INTERVAL)
                    continue
                else:
                    self._no_key_logged = False

                # ---------------- INIT STATE ----------------

                if not self._state_initialized:
                    print("[Poller] API key detected, syncing state...")
                    self.last_event_id = self._load_state()
                    self._state_initialized = True

                # ---------------- REQUEST ----------------

                response = self._request(
                    "POST",
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

                # ---------------- PAUSED ----------------

                self.worker.set_paused(data.get("paused"))

                # ---------------- WS ADDRESS ----------------

                ws_address = data.get("ws_address")
                self.worker.set_ws_address(ws_address)

                # ---------------- SKIP ----------------

                if data.get("skip"):
                    tts_runtime.stop()
                    request_stop()

                # ---------------- EVENTS ----------------

                events = data.get("events") or []

                for event in events:
                    ws_commands = event.get("ws_commands", [])
                    keep = []

                    for com in ws_commands:
                        if com.get("delay") == 0:
                            command = com.get("command")

                            if command and ws_address:
                                send_ws_command(command, ws_address)
                        else:
                            keep.append(com)

                    event["ws_commands"] = keep

                    if any([
                        event.get("alert"),
                        event.get("formatted_text"),
                        event.get("start_commands"),
                        event.get("end_commands"),
                        event.get("ws_commands"),
                    ]):
                        incomingEventQueue.add_event(event)

                # ---------------- LAST EVENT ID ----------------

                new_last_event_id = data.get("last_event_id")

                if new_last_event_id is not None:
                    try:
                        new_last_event_id = int(new_last_event_id)

                        if new_last_event_id != self.last_event_id:
                            self.last_event_id = new_last_event_id
                            self._save_state()

                    except:
                        pass

            # ---------------- ERRORS ----------------

            except requests.exceptions.ConnectionError:
                print("[Poller] connection lost")

            except requests.exceptions.Timeout:
                print("[Poller] timeout")

            except Exception as e:
                print(f"[Poller] unexpected error: {e}")

            time.sleep(POLL_INTERVAL)