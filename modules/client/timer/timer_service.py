import threading
import time

from .timer_state import timer_state
from .timer_ws import emit_time


class TimerService:

    # ---------- format ----------

    @staticmethod
    def _format(seconds: int) -> str:

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        sec = seconds % 60

        if hours < 99:
            return f"{hours:02d}:{minutes:02d}:{sec:02d}"

        return f"{hours:03d}:{minutes:02d}:{sec:02d}"

    # ---------- getters ----------

    @staticmethod
    def get_remaining_seconds() -> int:
        with timer_state.lock:
            return timer_state.current_seconds

    @staticmethod
    def get_formatted_time() -> str:
        with timer_state.lock:
            return TimerService._format(timer_state.current_seconds)

    # ---------- timer loop ----------

    @staticmethod
    def _loop():

        next_tick = time.time()

        while True:

            next_tick += 1
            time.sleep(max(0, next_tick - time.time()))

            with timer_state.lock:

                if not timer_state.is_running:
                    break

                timer_state.current_seconds -= timer_state.tick

                # ограничение нулём
                if timer_state.current_seconds <= 0:
                    timer_state.current_seconds = 0
                    timer_state.is_running = False

                current = timer_state.current_seconds

            emit_time(TimerService._format(current))

    # ---------- controls ----------

    @staticmethod
    def start():

        with timer_state.lock:

            if timer_state.is_running:
                return

            if timer_state.current_seconds <= 0:
                return

            timer_state.is_running = True

        thread = threading.Thread(
            target=TimerService._loop,
            daemon=True
        )

        with timer_state.lock:
            timer_state.timer_thread = thread

        thread.start()

        emit_time(TimerService.get_formatted_time())

    @staticmethod
    def stop():

        with timer_state.lock:
            timer_state.is_running = False

    # ---------- time ----------

    @staticmethod
    def set_time(seconds: int):

        with timer_state.lock:

            seconds = max(0, int(seconds))

            timer_state.total_seconds = seconds
            timer_state.current_seconds = seconds

        emit_time(TimerService._format(seconds))

    @staticmethod
    def add_time(seconds: int):

        with timer_state.lock:

            timer_state.current_seconds = max(
                0,
                timer_state.current_seconds + seconds
            )

            current = timer_state.current_seconds

        emit_time(TimerService._format(current))

    # ---------- pets ----------

    @staticmethod
    def apply_pets(tick: int, donate_boost: float):

        with timer_state.lock:

            timer_state.tick = max(0, int(tick))
            timer_state.donate_boost = float(donate_boost)

    # ---------- donate ----------

    @staticmethod
    def add_donate(amount: float):

        with timer_state.lock:
            seconds = int(amount * timer_state.donate_boost)

        TimerService.add_time(seconds)