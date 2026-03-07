import threading


class TimerState:

    def __init__(self):

        self.lock = threading.Lock()

        # время
        self.total_seconds = 0
        self.current_seconds = 1800

        # runtime
        self.is_running = False
        self.timer_thread = None

        # влияние петов
        self.tick = 1
        self.donate_boost = 1.0

        # websocket
        self.ws_url = None
        self.last_payload = None
        self.ws_lock = threading.Lock()


timer_state = TimerState()