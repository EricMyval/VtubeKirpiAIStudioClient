import threading


class PetState:

    def __init__(self):

        self.lock = threading.Lock()

        self.active_pet = None
        self.pet_thread = None

        self.stop_event = threading.Event()

        # дефолтные настройки таймера
        self.default_tick = 1
        self.default_donate_boost = 1.0


pet_state = PetState()