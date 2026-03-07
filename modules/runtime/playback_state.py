import threading


class PlaybackState:

    def __init__(self):

        # система на паузе или нет
        self.pause_event = threading.Event()
        self.pause_event.set()

        # сигнал пропуска текущего события
        self.skip_event = threading.Event()

    # ==============================
    # PAUSE
    # ==============================

    def pause(self):
        print("[Playback] pause")
        self.pause_event.clear()

    def resume(self):
        print("[Playback] resume")
        self.pause_event.set()

    # ==============================
    # SKIP
    # ==============================

    def skip(self):
        print("[Playback] skip")
        self.skip_event.set()

    def reset_skip(self):
        self.skip_event.clear()

    # ==============================

    def is_paused(self):
        return not self.pause_event.is_set()

    def is_skip(self):
        return self.skip_event.is_set()


playback_state = PlaybackState()