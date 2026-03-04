from typing import Optional, Callable
from modules.chat.chat_to_donation_settings import ChatToDonationControllerSettings
from modules.phrases.phrases import MESSAGE_FROM_VOICE
from modules.afk.afk_settings import afk_settings
from modules.web_sockets.sender import send_ws_command


class AFKState:
    def __init__(self):
        self._enabled = False
        self.execute_donation = None
        self.chat_to_donation_settings = None

    def enable(self):
        self._enabled = True
        print("🟡 AFK режим ВКЛЮЧЕН")

        command = afk_settings.get("ws_on_enable")
        if command:
            send_ws_command(command)

        # Вступительная фраза
        if self.execute_donation and self.chat_to_donation_settings:
            self.execute_donation(
                "",
                self.chat_to_donation_settings.afk_intro_text,
                MESSAGE_FROM_VOICE
            )

    def disable(self):
        self._enabled = False
        print("🟢 AFK режим ВЫКЛЮЧЕН")

        command = afk_settings.get("ws_on_disable")
        if command:
            send_ws_command(command)

    def toggle(self) -> bool:
        if self._enabled:
            self.disable()
        else:
            self.enable()
        return self._enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def set_execute(
        self,
        execute_donation: Optional[Callable[[str, str, str], None]],
        chat_settings: ChatToDonationControllerSettings
    ):
        self.execute_donation = execute_donation
        self.chat_to_donation_settings = chat_settings


afk_state = AFKState()
