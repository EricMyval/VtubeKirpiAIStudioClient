# modules/client/donate_panel/donate_panel_state.py

import threading


class DonatePanelState:

    def __init__(self):

        self._lock = threading.Lock()

        self._current_donate = None
        self._paused = False

    # ======================================
    # CURRENT DONATE
    # ======================================

    def get_current(self):

        with self._lock:
            return self._current_donate

    def set_current(self, donate):

        with self._lock:
            self._current_donate = donate

    def clear_current(self):

        with self._lock:
            self._current_donate = None

    # ======================================
    # PAUSE
    # ======================================

    def is_paused(self):

        with self._lock:
            return self._paused

    def toggle_pause(self):

        with self._lock:
            self._paused = not self._paused
            return self._paused


donate_panel_state = DonatePanelState()