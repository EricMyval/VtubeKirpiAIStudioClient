from .repository import DonateRepository
from .donate_panel_state import donate_panel_state
from .session_stats import donation_session_stats


class DonatePanelService:

    # ==========================================================
    # ADD DONATE FROM POLLER
    # ==========================================================

    def add_event_from_poller(self, event: dict):

        amount = int(event.get("amount", 0) or 0)

        if amount <= 0:
            return

        username = event.get("username") or event.get("user") or "unknown"
        message = event.get("message") or ""
        platform = event.get("platform") or "unknown"

        DonateRepository.add(
            platform=platform,
            username=username,
            amount=amount,
            message=message,
        )

        donation_session_stats.add(amount)

    # ==========================================================
    # MARK PLAYING
    # ==========================================================

    def mark_playing(self, event: dict):

        amount = int(event.get("amount", 0) or 0)

        if amount <= 0:
            return

        username = event.get("username") or event.get("user") or "unknown"

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