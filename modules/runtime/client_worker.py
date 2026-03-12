import threading
import time
from modules.runtime.client_queue import clientEventQueue
from modules.utils.constant import PLATFORM_TYPE_TWITCH_POINTS
from modules.utils.donate_panel_api import set_active_donate, clear_active_donate
from modules.utils.ws_client import send_ws_command
from modules.tts.tts_runtime import tts_runtime
from modules.alerts.alert_service import alert_service
from modules.alerts.alert_queue import push_alert


class ClientWorker:
    def __init__(self, queue):
        self.queue = queue
        self.ws_address = "ws://127.0.0.1:19190/"
        self.thread = threading.Thread(
            target=self._loop,
            daemon=True
        )

    def _execute_event(self, event: dict):
        platform = event.get("platform")

        # DONATE PANEL START
        event_id = event.get("id")
        if event_id:
            set_active_donate(event_id)

        # TTS PREPARE (WAIT FIRST SEGMENT)
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
        self._execute_ws_command_list(event.get("start_commands"))

        # TTS PLAY (BLOCK UNTIL FINISHED)
        if first_segment:
            try:
                tts_runtime.play(first_segment)
            except Exception as e:
                print("[TTS] play error:", e)

        # END WS COMMANDS
        self._execute_ws_command_list(event.get("end_commands"))

        # WS COMMANDS
        self._execute_ws_command_list(event.get("ws_commands"))

    # ======================================

    def _execute_ws_command_list(self, commands):
        if commands and self.ws_address:
            for cmd in commands:
                command_text = cmd.get("command")
                delay = cmd.get("delay", 0)
                if command_text:
                    send_ws_command(command_text, self.ws_address)
                if delay and delay > 0:
                    end_time = time.time() + delay
                    while time.time() < end_time:
                        time.sleep(0.1)

    def start(self):
        self.thread.start()

    def set_ws_address(self, url: str):
        if url and url != self.ws_address:
            self.ws_address = url

    def _loop(self):
        while True:
            event = self.queue.get_event()
            try:
                self._execute_event(event)
            except Exception as e:
                print(f"[ClientWorker] error: {e}")
            finally:
                clear_active_donate()
            self.queue.task_done()


clientWorker = ClientWorker(clientEventQueue)
clientWorker.start()