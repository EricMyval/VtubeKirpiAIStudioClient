# modules/alerts/alert_control.py

import threading

_stop = False
_lock = threading.Lock()

def request_stop():
    global _stop
    with _lock:
        _stop = True

def pull_stop():
    global _stop
    with _lock:
        if _stop:
            _stop = False
            return True
        return False