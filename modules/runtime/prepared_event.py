class PreparedEvent:

    def __init__(self, event, segment_queue=None):
        self.event = event
        self.segment_queue = segment_queue