import threading

_queue = []
_lock = threading.Lock()


def push_alert(payload: dict):
    if not payload:
        return

    with _lock:
        _queue.append(payload)


def pull_alert():
    with _lock:
        if not _queue:
            return None
        return _queue.pop(0)