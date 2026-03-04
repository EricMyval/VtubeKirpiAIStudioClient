from threading import Event, Lock
from typing import Optional, Callable


class PlaybackController:
    """
    Контроллер текущего воспроизведения доната.
    Отвечает ТОЛЬКО за runtime-состояние.
    """

    def __init__(self):
        self.stop_event = Event()
        self._lock = Lock()
        self._last_callback: Optional[Callable[[], None]] = None
        self._active = False

    # ======================================================
    # Lifecycle
    # ======================================================

    def start_donation(self, last_callback: Optional[Callable[[], None]]):
        """
        Вызывается ПЕРЕД началом воспроизведения доната.
        Регистрирует last_playback_actions.
        """
        with self._lock:
            self.stop_event.clear()
            self._last_callback = last_callback
            self._active = True

    def finish_donation(self):
        """
        Вызывается после НОРМАЛЬНОГО окончания доната.
        """
        with self._lock:
            self._last_callback = None
            self._active = False
            self.stop_event.clear()

    # ======================================================
    # External control (admin)
    # ======================================================

    def force_stop(self):
        """
        Принудительно запрашивает остановку текущего доната.
        last_callback будет вызван worker'ом,
        в правильном потоке и ровно один раз.
        """
        with self._lock:
            if not self._active:
                return

            # только сигнал остановки
            self.stop_event.set()

    # ======================================================
    # State
    # ======================================================

    def is_active(self) -> bool:
        return self._active


# Singleton
playback_controller = PlaybackController()
