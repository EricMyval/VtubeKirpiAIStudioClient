import threading
import time

from modules.afk.afk_state import afk_state
from modules.client.roulette.runtime import roulette_runtime
from modules.client.runtime.client_queue import clientEventQueue
from modules.client.runtime.constant import PLATFORM_TYPE_DONATION_ALERTS, PLATFORM_TYPE_DONATION_ALERTS_AI, \
    PLATFORM_TYPE_DONATTY, PLATFORM_TYPE_DONATTY_AI, PLATFORM_TYPE_TWITCH_VOICE, PLATFORM_TYPE_TWITCH_AI
from modules.client.runtime.ws_client import send_ws_command
from modules.client.tts.tts_runtime import tts_runtime
from modules.donation_image.donation_image import show_message_image
from modules.client.alerts.alert_service import alert_service
from modules.client.alerts.alert_queue import push_alert
from modules.client.donate_panel.donate_panel_service import donate_panel_service


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

            try:
                self._execute_event(event)
            except Exception as e:
                print(f"[ClientWorker] error: {e}")

            self.queue.task_done()

    # ======================================

    def _execute_event(self, event: dict):

        amount = int(event.get("amount", 0) or 0)

        is_donate = amount > 0

        # ======================================
        # DONATE PANEL START
        # ======================================

        donate_panel_service.mark_playing(event)

        # ======================================
        # ALERT
        # ======================================

        if event.get("alert"):

            payload = alert_service.build_payload(event)
            push_alert(payload)

        # ======================================
        # START WS COMMANDS
        # ======================================

        self._execute_ws_command_list(event.get("start_commands", []))

        # ======================================
        # IMAGE
        # ======================================

        if event.get("image_url"):

            show_message_image(
                event["image_url"],
                amount
            )

        # ======================================
        # ROULETTE
        # ======================================

        if is_donate:
            roulette_runtime.add_amount(amount)

        # ======================================
        # TTS
        # ======================================

        platform = event.get("platform")
        if platform and platform in {
            PLATFORM_TYPE_DONATION_ALERTS,
            PLATFORM_TYPE_DONATION_ALERTS_AI,
            PLATFORM_TYPE_DONATTY,
            PLATFORM_TYPE_DONATTY_AI,
            PLATFORM_TYPE_TWITCH_VOICE,
            PLATFORM_TYPE_TWITCH_AI
        }:
            text = event.get("formatted_text")
            voice_file_path = event.get("voice_file_path")
            voice_reference_text = event.get("voice_reference_text")
            if text and voice_file_path and voice_reference_text:
                try:
                    tts_runtime.speak(
                        text,
                        voice_file_path,
                        voice_reference_text
                    )
                except Exception as e:
                    print(f"[TTS] error: {e}")

        # ======================================
        # WS COMMANDS
        # ======================================

        self._execute_ws_command_list(event.get("ws_commands", []))

        # ======================================
        # END WS COMMANDS
        # ======================================

        self._execute_ws_command_list(event.get("end_commands", []))

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

        afk_on = afk_state.is_enabled()

        for cmd in commands:

            afk_only = cmd.get("afk_only", False)

            if afk_only and not afk_on:
                continue

            command_text = cmd.get("command")
            delay = cmd.get("delay", 0)

            if command_text:

                try:
                    send_ws_command(command_text, self.ws_address)

                except Exception as e:
                    print(f"[WS] send error: {e}")

            if delay and delay > 0:
                time.sleep(delay)

clientWorker = ClientWorker(clientEventQueue)
clientWorker.start()