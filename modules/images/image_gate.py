import threading


class ImageGate:

    def __init__(self):
        self._event = threading.Event()

    def wait(self):
        self._event.clear()
        self._event.wait()

    def release(self):
        self._event.set()


image_gate = ImageGate()