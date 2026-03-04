# modules/client/roulette/runtime.py

from threading import Lock
from collections import deque
import time
import uuid

from modules.client.roulette.engine import RouletteEngine
from modules.client.roulette.config_repo import RouletteConfigRepository
from modules.client.runtime.config_loader import ClientConfigLoader


class RouletteRuntime:

    def __init__(self):
        self._lock = Lock()

        self.current_sum = 0
        self.tasks = []
        self.spin_queue = deque()

        # repo + engine
        self._repo = RouletteConfigRepository()
        self._engine = RouletteEngine(self._repo)

        # загрузка конфига при старте
        self._load_config()

    # =====================================================
    # CONFIG
    # =====================================================

    def _load_config(self):
        """
        Загружаем конфиг рулетки с сервера.
        """
        try:
            data = ClientConfigLoader.load_roulette_config()
            self._repo.set_from_api(data)
            print("[Roulette] Config loaded")
        except Exception as e:
            print("[Roulette] Config load failed:", e)

    def reload_config(self):
        """
        Можно вызывать вручную или по таймеру.
        """
        try:
            data = ClientConfigLoader.load_roulette_config()
            self._repo.set_from_api(data)
            print("[Roulette] Config reloaded")
        except Exception as e:
            print("[Roulette] Reload failed:", e)

    # =====================================================
    # MAIN ENTRY (донаты / баллы)
    # =====================================================

    def add_amount(self, value: int):

        if value <= 0:
            return 0

        # рулетка отключена
        if not self._repo.is_enabled():
            return 0

        with self._lock:
            self.current_sum += int(value)

        # считаем прокрутки
        results = self._engine.push_amount(int(value))

        items = self._repo.get_items()

        for r in results:

            visual_items = [
                {"title": i.title}
                for i in items
            ]

            win_index = next(
                (idx for idx, i in enumerate(items) if i.id == r.item.id),
                0
            )

            self.push_spin({
                "items": visual_items,
                "win_index": win_index
            })

        return len(results)

    # =====================================================
    # SPINS (для overlay)
    # =====================================================

    def push_spin(self, payload: dict):
        with self._lock:
            self.spin_queue.append(payload)

    def pop_spin(self):
        with self._lock:
            if not self.spin_queue:
                return None
            return self.spin_queue.popleft()

    # =====================================================
    # PROGRESS
    # =====================================================

    def reset_progress(self):
        with self._lock:
            self.current_sum = 0

    def get_sum(self):
        with self._lock:
            return self.current_sum

    # =====================================================
    # TASKS
    # =====================================================

    def add_task(self, title: str):

        task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "time": int(time.time())
        }

        with self._lock:
            self.tasks.append(task)

        return task

    def remove_task(self, task_id: str):
        with self._lock:
            self.tasks = [t for t in self.tasks if t["id"] != task_id]

    def get_tasks(self):
        with self._lock:
            return list(self.tasks)


# единый экземпляр
roulette_runtime = RouletteRuntime()