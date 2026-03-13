import queue


class IncomingEventQueue:

    def __init__(self):
        self.q = queue.Queue()

    def add_event(self, event: dict):
        self.q.put(event)

    def get_event(self):
        return self.q.get()

    def task_done(self):
        self.q.task_done()


incomingEventQueue = IncomingEventQueue()