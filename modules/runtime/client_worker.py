import threading
import time

from modules.pets.pet_runtime import handle_pet
from modules.runtime.client_queue import clientEventQueue
from modules.runtime.playback_state import playback_state

from modules.utils.constant import PLATFORM_TYPE_TWITCH_POINTS
from modules.utils.ws_client import send_ws_command

from modules.timer.timer_service import TimerService
from modules.tts.tts_runtime import tts_runtime

from modules.alerts.alert_service import alert_service
from modules.alerts.alert_queue import push_alert

from modules.donate_panel.donate_panel_service import donate_panel_service

from modules.images.show_image import show_message_image
from modules.images.image_gate import image_gate


class ClientWorker:

    def __init__(self, queue):

        self.queue = queue
        self.ws_address = "ws://127.0.0.1:19190/"

        self.thread = threading.Thread(
            target=self._loop,
            daemon=True
        )

    # ======================================

    def start(self):
        self.thread.start()

    # ======================================

    def set_ws_address(self, url: str):

        if url and url != self.ws_address:
            print(f"🌐 WS address updated: {url}")
            self.ws_address = url

    # ======================================

    def _loop(self):

        while True:

            event = self.queue.get_event()

            # если пауза — не начинаем обработку
            while playback_state.is_paused():
                time.sleep(0.1)

            # новый ивент → сбрасываем skip
            playback_state.reset_skip()

            try:
                self._execute_event(event)
            except Exception as e:
                print(f"[ClientWorker] error: {e}")

            self.queue.task_done()

    # ======================================

    def _execute_event(self, event: dict):

        platform = event.get("platform")
        amount = int(event.get("amount", 0) or 0)
        is_donate = amount > 0

        # ======================================
        # DONATE PANEL START
        # ======================================

        donate_panel_service.mark_playing(event)

        # ======================================
        # TTS PREPARE
        # ======================================

        first_segment = None
        tts_enabled = False

        if platform and platform not in {PLATFORM_TYPE_TWITCH_POINTS}:

            text = event.get("formatted_text")
            voice_file_path = event.get("voice_file_path")
            voice_reference_text = event.get("voice_reference_text")

            if text and voice_file_path and voice_reference_text:

                tts_enabled = True

                first_segment = tts_runtime.prepare(
                    text,
                    voice_file_path,
                    voice_reference_text
                )

                if playback_state.is_skip():
                    tts_runtime.stop()

        # ======================================
        # ALERT
        # ======================================

        if event.get("alert"):
            payload = alert_service.build_payload(event)
            push_alert(payload)

            alert_duration = int(payload.get("duration", 6000))
            tts_after_alert = payload.get("tts_after", False)

            if tts_after_alert:
                time.sleep(int(alert_duration / 1000))

        # ======================================
        # START WS COMMANDS
        # ======================================

        self._execute_ws_command_list(event.get("start_commands", []))

        # ======================================
        # IMAGE SHOW
        # ======================================

        if event.get("image_url"):
            show_message_image(
                event["image_url"],
                self.ws_address
            )

        # ======================================
        # PET
        # ======================================

        handle_pet(event, self.ws_address)

        # ======================================
        # TIMER DONATE
        # ======================================

        if is_donate:
            TimerService.add_donate(amount)

        # ======================================
        # TTS
        # ======================================

        if tts_enabled and first_segment:

            if playback_state.is_skip():
                tts_runtime.stop()
            else:
                tts_runtime.play(first_segment)

        if playback_state.is_skip():
            tts_runtime.stop()

        # ======================================
        # END WS COMMANDS
        # ======================================

        self._execute_ws_command_list(event.get("end_commands", []))

        # ======================================
        # WS COMMANDS
        # ======================================

        self._execute_ws_command_list(event.get("ws_commands", []))

        # ======================================
        # IMAGE WAIT
        # ======================================

        if event.get("image_url"):
            image_gate.wait()

        # ======================================
        # DONATE PANEL END
        # ======================================

        donate_panel_service.mark_finished()

    # ======================================

    def _execute_ws_command_list(self, commands: list[dict]):

        if not commands:
            return

        if not self.ws_address:
            print("[WS] ws_address not set")
            return

        for cmd in commands:

            command_text = cmd.get("command")
            delay = cmd.get("delay", 0)

            if command_text:
                try:
                    send_ws_command(command_text, self.ws_address)
                except Exception as e:
                    print(f"[WS] send error: {e}")

            if delay and delay > 0:

                waited = 0

                while waited < delay:

                    if playback_state.is_skip():
                        break

                    time.sleep(0.1)
                    waited += 0.1


clientWorker = ClientWorker(clientEventQueue)
clientWorker.start()