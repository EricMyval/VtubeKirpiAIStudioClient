# utils/donation_checker.py
from modules.config.config import cfg
from modules.config.config_loader import Config

class DonationChecker:
    def __init__(self, config: Config):
        self.config = config

    def is_ai_donation(self, amount: int) -> bool:
        """Проверяет, является ли донат ИИ-донатом"""
        donation_config = self.config.get_donation_config()
        return donation_config["ai_min"] <= amount <= donation_config["ai_max"]

    def get_ai_donation(self) -> int:
        donation_config = self.config.get_donation_config()
        return donation_config["ai_max"]

    def get_donation_type(self, amount: int) -> str:
        """Возвращает тип доната"""
        if not self.is_in_range(amount):
            return "ignored"
        elif self.is_ai_donation(amount):
            return "ai"
        else:
            return "regular"

donation_checker = DonationChecker(cfg)