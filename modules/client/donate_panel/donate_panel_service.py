from typing import Optional

from .repository import DonateRepository
from .queue_runtime import donate_queue_runtime
from .donate_panel_state import donate_panel_state
from .session_stats import donation_session_stats


class DonatePanelService:

    # ==========================================================
    # API EVENT
    # ==========================================================

    def add_from_event(self, event: dict):

        username = event.get("username") or event.get("user") or "unknown"
        message = event.get("message") or ""
        amount = int(event.get("amount", 0) or 0)

        platform = event.get("platform") or "unknown"

        donate_id = DonateRepository.add(
            platform=platform,
            username=username,
            amount=amount,
            message=message,
        )

        donate_queue_runtime.push(donate_id)

        # если ничего не играет — запускаем донат
        if not donate_panel_state.current_donate:
            self.next()

    # ==========================================================
    # current donate
    # ==========================================================

    def get_current(self):

        return donate_panel_state.current_donate

    # ==========================================================
    # next donate
    # ==========================================================

    def next(self):

        donate_id = donate_queue_runtime.pop()

        if not donate_id:
            donate_panel_state.current_donate = None
            return None

        donate = DonateRepository.get_by_id(donate_id)

        if not donate:
            return None

        DonateRepository.update_status(donate.id, "playing")

        donate_panel_state.current_donate = donate

        return donate

    # ==========================================================
    # finish donate
    # ==========================================================

    def finish(self):

        donate = donate_panel_state.current_donate

        if not donate:
            return

        DonateRepository.update_status(donate.id, "played")

        donate_panel_state.current_donate = None

    # ==========================================================
    # skip
    # ==========================================================

    def skip(self):

        donate = donate_panel_state.current_donate

        if not donate:
            return

        DonateRepository.update_status(donate.id, "skipped")

        donate_panel_state.current_donate = None

    # ==========================================================
    # pause
    # ==========================================================

    def toggle_pause(self):

        donate_panel_state.paused = not donate_panel_state.paused

    # ==========================================================
    # stats
    # ==========================================================

    def get_session_total(self):

        return donation_session_stats.get_total()

    # ==========================================================
    # history
    # ==========================================================

    def get_history(self, limit=50):

        return DonateRepository.get_all(limit)


donate_panel_service = DonatePanelService()