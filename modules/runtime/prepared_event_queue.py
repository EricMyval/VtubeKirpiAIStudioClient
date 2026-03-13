import queue


class PreparedEventQueue:

    def __init__(self):
        self.q = queue.Queue()

    def add(self, prepared_event):
        self.q.put(prepared_event)

    def get(self):
        return self.q.get()

    def task_done(self):
        self.q.task_done()

preparedEventQueue = PreparedEventQueue()