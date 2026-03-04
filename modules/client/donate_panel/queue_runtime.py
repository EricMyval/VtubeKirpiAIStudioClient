import queue


class DonateQueueRuntime:

    def __init__(self):

        self.queue = queue.Queue()

    def push(self, donate_id: int):

        self.queue.put(donate_id)

    def pop(self):

        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None

    def size(self):

        return self.queue.qsize()


donate_queue_runtime = DonateQueueRuntime()