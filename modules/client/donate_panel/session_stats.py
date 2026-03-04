import threading


class DonationSessionStats:

    def __init__(self):

        self._lock = threading.Lock()
        self._total_amount = 0

    # ======================================
    # RESET
    # ======================================

    def reset(self):

        with self._lock:
            self._total_amount = 0

    # ======================================
    # ADD
    # ======================================

    def add(self, amount: int):

        try:
            value = int(amount)
        except Exception:
            return

        with self._lock:
            self._total_amount += value

    # ======================================
    # GET TOTAL
    # ======================================

    def get_total(self) -> int:

        with self._lock:
            return int(self._total_amount)


donation_session_stats = DonationSessionStats()