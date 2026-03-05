import threading


class AFKState:

    def __init__(self):

        self._enabled = False
        self._lock = threading.Lock()

    # =============================

    def set_enabled(self, value: bool):

        with self._lock:
            self._enabled = bool(value)

    # =============================

    def is_enabled(self) -> bool:

        with self._lock:
            return self._enabled


afk_state = AFKState()