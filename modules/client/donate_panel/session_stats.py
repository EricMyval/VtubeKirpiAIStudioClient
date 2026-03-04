class DonationSessionStats:

    def __init__(self):
        self.total_amount = 0

    def reset(self):
        self.total_amount = 0

    def add(self, amount: int):

        try:
            self.total_amount += int(amount)
        except Exception:
            pass

    def get_total(self) -> int:
        return self.total_amount


donation_session_stats = DonationSessionStats()