import json

from .repository import DonateRepository
from .donate_panel_state import donate_panel_state
from .session_stats import donation_session_stats

from modules.client.images.image_gate import image_gate
from modules.client.images.show_image import hide_message_image

from modules.client.runtime.client_queue import clientEventQueue

from modules.utils.constant import (
    PLATFORM_TYPE_TWITCH_POINTS,
    PLATFORM_TYPE_TWITCH_VOICE,
    PLATFORM_TYPE_TWITCH_AI,
    PLATFORM_TYPE_DONATION_ALERTS,
    PLATFORM_TYPE_DONATION_ALERTS_AI,
    PLATFORM_TYPE_DONATTY,
    PLATFORM_TYPE_DONATTY_AI
)


class DonatePanelService:

    # ==========================================================
    # ADD DONATE FROM POLLER
    # ==========================================================

    def add_event_from_poller(self, event: dict):

        platform = event.get("platform") or "unknown"

        amount = int(event.get("amount", 0) or 0)

        if amount <= 0 and platform in {
            PLATFORM_TYPE_TWITCH_POINTS,
            PLATFORM_TYPE_TWITCH_VOICE,
            PLATFORM_TYPE_TWITCH_AI
        }:
            amount = int(event.get("settings", {}).get("points", 0) or 0)

        if amount <= 0:
            return

        username = event.get("username") or event.get("user") or "unknown"
        message = event.get("message") or ""

        extra = None

        if platform in {
            PLATFORM_TYPE_TWITCH_POINTS,
            PLATFORM_TYPE_TWITCH_VOICE,
            PLATFORM_TYPE_TWITCH_AI
        }:
            extra = event.get("reward")

        DonateRepository.add(
            platform=platform,
            username=username,
            amount=amount,
            message=message,
            extra=extra,
            raw_event=json.dumps(event)
        )

        if platform in {
            PLATFORM_TYPE_DONATION_ALERTS,
            PLATFORM_TYPE_DONATION_ALERTS_AI,
            PLATFORM_TYPE_DONATTY,
            PLATFORM_TYPE_DONATTY_AI
        }:
            donation_session_stats.add(amount)

    # ==========================================================
    # START EVENT FROM PANEL
    # ==========================================================

    def start_event(self, donate_id: int):

        donate = DonateRepository.get_by_id(donate_id)

        if not donate:
            return False

        if not donate.raw_event:
            return False

        event = json.loads(donate.raw_event)

        # передаем ID доната
        event["_donate_id"] = donate_id

        clientEventQueue.add_event(event)

        return True

    # ==========================================================
    # IMAGE CONTINUE
    # ==========================================================

    def image_continue(self, ws_url: str):

        hide_message_image(ws_url)
        image_gate.release()

    # ==========================================================
    # MARK PLAYING
    # ==========================================================

    def mark_playing(self, event: dict):

        print("PLAYING", event.get("_donate_id"))

        username = event.get("user") or event.get("username")
        amount = int(event.get("amount", 0) or 0)

        donate = DonateRepository.find_last(username, amount)

        if not donate:
            return

        DonateRepository.update_status(
            donate.id,
            "playing"
        )

        donate_panel_state.set_current(donate)

    # ==========================================================
    # MARK FINISHED
    # ==========================================================

    def mark_finished(self):

        print("FINISHED")

        donate = donate_panel_state.get_current()

        if not donate:
            return

        DonateRepository.update_status(
            donate.id,
            "played"
        )

        donate_panel_state.clear_current()

    # ==========================================================
    # SKIP
    # ==========================================================

    def skip(self):

        donate = donate_panel_state.get_current()

        if not donate:
            return

        DonateRepository.update_status(
            donate.id,
            "skipped"
        )

        donate_panel_state.clear_current()

    # ==========================================================
    # PAUSE
    # ==========================================================

    def toggle_pause(self):

        return donate_panel_state.toggle_pause()

    # ==========================================================
    # PAUSED STATE
    # ==========================================================

    def is_paused(self):

        return donate_panel_state.is_paused()

    # ==========================================================
    # CURRENT
    # ==========================================================

    def get_current(self):

        return donate_panel_state.get_current()

    # ==========================================================
    # SESSION TOTAL
    # ==========================================================

    def get_session_total(self):

        return donation_session_stats.get_total()

    # ==========================================================
    # HISTORY
    # ==========================================================

    def get_history(self, limit=50):

        return DonateRepository.get_all(limit)


donate_panel_service = DonatePanelService()