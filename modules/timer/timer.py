import asyncio
import threading
import time
from typing import Dict, Any, Optional
from modules.web_sockets.sender import send_ws_command_async

class Timer:
    def __init__(self, hours=0, minutes=30, seconds=0):
        self.total_seconds = hours * 3600 + minutes * 60 + seconds
        self.current_time = self.total_seconds

        self.is_running = False
        self.timer_thread: Optional[threading.Thread] = None

        # актуальное влияние петов
        self._pets_influence: Dict[str, Any] = {
            "tick": 1,
            "freeze": False,
        }

        self.lock = threading.Lock()

        # ws
        self._last_sent_payload = None
        self._send_lock = threading.Lock()

    # ---------- COMPAT ----------
    @property
    def subtract_per_tick(self) -> int:
        """
        Для совместимости со старым кодом.
        НИ НА ЧТО НЕ ВЛИЯЕТ.
        """
        return 0 if self._pets_influence["freeze"] else self._pets_influence["tick"]

    # ---------- format ----------

    def format_time(self) -> str:
        hours = self.current_time // 3600
        minutes = (self.current_time % 3600) // 60
        seconds = self.current_time % 60
        if hours < 99:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{hours:03d}:{minutes:02d}:{seconds:02d}"

    # ---------- websocket ----------

    def send_ws_command(self, message: str) -> None:
        with self._send_lock:
            if message == self._last_sent_payload:
                return
            self._last_sent_payload = message

        def runner():
            try:
                asyncio.run(send_ws_command_async(message))
            except Exception as e:
                print(f"[Timer][WebSocket ERROR]: {e}")

        threading.Thread(target=runner, daemon=True).start()

    def _emit_time(self) -> None:
        self.send_ws_command(
            f'{{"action":"timer","data":"{self.format_time()}"}}'
        )

    # ---------- pets influence ----------

    def apply_pets_influence(self, pets_params: Dict[str, Any]) -> None:
        with self.lock:
            self._pets_influence["freeze"] = bool(pets_params.get("freeze", False))
            self._pets_influence["tick"] = int(pets_params.get("tick", 1)) or 1

    # ---------- timer loop ----------

    def timer_loop(self) -> None:
        while True:
            time.sleep(1)

            with self.lock:
                if not self.is_running:
                    break

                if not self._pets_influence["freeze"]:
                    self.current_time -= self._pets_influence["tick"]

                if self.current_time < -1:
                    self.current_time = -1

                if self.current_time >= 0:
                    self._emit_time()

    # ---------- controls ----------

    def start(self) -> None:
        with self.lock:
            if self.is_running or self.current_time <= 0:
                return

            self.is_running = True

        # если пет был активен ДО старта
        # влияние должно сохраниться
        print("[Timer] start with influence:", self._pets_influence)

        self.timer_thread = threading.Thread(
            target=self.timer_loop,
            daemon=True
        )
        self.timer_thread.start()
        self._emit_time()

    def stop(self) -> None:
        with self.lock:
            if self.is_running:
                self.is_running = False
                print("Таймер остановлен")

    # ---------- donations ----------

    def add_donate_with_pets(
        self,
        pets_params: Dict[str, Any],
        amount_user: str
    ) -> None:
        amount = int(float(amount_user))
        boost = float(pets_params.get("donate_boost", 1.0))

        self.apply_pets_influence(pets_params)

        if not pets_params.get("freeze", False):
            self.add_time(int(amount * boost))

    def add_time(self, seconds: int) -> None:
        if seconds <= 0:
            return

        with self.lock:
            self.current_time += seconds
            print(f"Добавлено {seconds} сек. Новое время: {self.format_time()}")
            self._emit_time()

    # ---------- getters ----------

    def get_remaining_time(self) -> int:
        with self.lock:
            return self.current_time

    def get_formatted_time(self) -> str:
        with self.lock:
            return self.format_time()

timer = Timer(hours=0, minutes=30, seconds=0)
