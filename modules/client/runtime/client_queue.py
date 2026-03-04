# modules/client/runtime/client_queue.py

import queue
from threading import Lock


class ClientEventQueue:

    def __init__(self):
        self._queue = queue.Queue()
        self._lock = Lock()

    def add_event(self, event: dict):
        self._queue.put(event)

    def get_event(self):
        return self._queue.get()

    def task_done(self):
        self._queue.task_done()

clientEventQueue = ClientEventQueue()