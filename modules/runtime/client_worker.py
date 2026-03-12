import threading
import time
from modules.runtime.client_queue import clientEventQueue
from modules.utils.constant import PLATFORM_TYPE_TWITCH_POINTS, PAUSED_INTERVAL
from modules.utils.donate_panel_api import set_active_donate, clear_active_donate
from modules.utils.ws_client import send_command_list
from modules.tts.tts_runtime import tts_runtime
from modules.alerts.alert_service import alert_service
from modules.alerts.alert_queue import push_alert

class ClientWorker:
    def __init__(self, queue):
        self.queue = queue
        self.paused = False
        self.ws_address = "ws://127.0.0.1:19190/"
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _execute_event(self, event: dict):
        # TTS PREPARE
        platform = event.get("platform")
        first_segment = None
        if platform != PLATFORM_TYPE_TWITCH_POINTS:
            text = event.get("formatted_text")
            voice_file_path = event.get("voice_file_path")
            voice_reference_text = event.get("voice_reference_text")
            if text and voice_file_path and voice_reference_text:
                try:
                    first_segment = tts_runtime.prepare(text, voice_file_path, voice_reference_text)
                except Exception as e:
                    print("[TTS] prepare error:", e)
        # ALERT
        if event.get("alert"):
            payload = alert_service.build_payload(event)
            push_alert(payload)
            if payload.get("tts_after", False):
                time.sleep(int(payload.get("duration", 6000)) / 1000)
        # START WS COMMANDS
        send_command_list(event.get("start_commands"), self.ws_address)
        # TTS PLAY
        if first_segment is not None:
            try:
                tts_runtime.play(first_segment)
            except Exception as e:
                print("[TTS] play error:", e)
        # END WS COMMANDS
        send_command_list(event.get("end_commands"), self.ws_address)
        # WS COMMANDS
        send_command_list(event.get("ws_commands"), self.ws_address)

    # ======================================

    def set_ws_address(self, url: str):
        if url and url != self.ws_address:
            self.ws_address = url

    def set_paused(self, paused: bool):
        if paused != self.paused:
            self.paused = paused == True

    def _loop(self):
        while True:
            event = self.queue.get_event()
            try:
                # DONATE PANEL START
                event_id = event.get("id")
                if event_id:
                    set_active_donate(event_id)
                # PAUSED
                while self.paused:
                    time.sleep(PAUSED_INTERVAL)
                self._execute_event(event)
            except Exception as e:
                print(f"[ClientWorker] error: {e}")
            finally:
                # DONATE PANEL STOP
                clear_active_donate()
            self.queue.task_done()

clientWorker = ClientWorker(clientEventQueue)