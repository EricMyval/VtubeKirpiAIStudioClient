import threading
import time
from modules.runtime.prepared_event_queue import preparedEventQueue
from modules.utils.constant import PAUSED_INTERVAL
from modules.utils.ws_client import send_command_list
from modules.utils.donate_panel_api import set_active_donate, clear_active_donate
from modules.tts.tts_runtime import tts_runtime
from modules.alerts.alert_service import alert_service
from modules.alerts.alert_queue import push_alert

class ClientWorker:
    def __init__(self):
        self.paused = False
        self.ws_address = "ws://127.0.0.1:19190/"
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def set_paused(self, paused):
        self.paused = paused is True

    def set_ws_address(self, url):
        if url and url != self.ws_address:
            self.ws_address = url

    def _execute_event(self, prepared_event):
        event = prepared_event.event
        segment_queue = prepared_event.segment_queue

        if event.get("alert"):
            payload = alert_service.build_payload(event)
            push_alert(payload)
            if payload.get("tts_after"):
                time.sleep(int(payload.get("duration", 6000)) / 1000)

        first_segment = None
        if segment_queue:
            try:
                first_segment = segment_queue.get(timeout=120)
            except:
                print("[TTS] first segment timeout")

        send_command_list(event.get("start_commands"), self.ws_address)

        if first_segment:
            tts_runtime.play(first_segment, segment_queue)

        send_command_list(event.get("end_commands"), self.ws_address)
        send_command_list(event.get("ws_commands"), self.ws_address)

    def _loop(self):
        while True:
            prepared_event = preparedEventQueue.get()
            try:
                event_id = prepared_event.event.get("id")
                if event_id:
                    set_active_donate(event_id)
                while self.paused:
                    time.sleep(PAUSED_INTERVAL)
                self._execute_event(prepared_event)
            except Exception as e:
                print("[ClientWorker error]", e)
            finally:
                clear_active_donate()
                preparedEventQueue.task_done()
                time.sleep(PAUSED_INTERVAL)

clientWorker = ClientWorker()