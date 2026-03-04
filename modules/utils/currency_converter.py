import json
from pathlib import Path

RATES_FILE = Path("data/db/currency_rates.json")

DEFAULT_RATES = {
    "RUB": 1,
    "USD": 80,
    "EUR": 90,
    "BYN": 30,
    "UAH": 2.5,
    "KZT": 0.2,
    "PLN": 24,
    "TRY": 2.7,
    "BRL": 18,
}

class CurrencyConverter:
    _rates: dict[str, float] | None = None

    # ---------------------------
    # internal
    # ---------------------------

    @classmethod
    def _ensure_file(cls):
        """
        Создаёт файл с дефолтными курсами, если его нет
        """
        if not RATES_FILE.exists():
            RATES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(RATES_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_RATES, f, ensure_ascii=False, indent=2)

    @classmethod
    def _load_rates(cls) -> dict[str, float]:
        cls._ensure_file()

        try:
            with open(RATES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # базовая валидация
            if not isinstance(data, dict) or "RUB" not in data:
                raise ValueError("Invalid currency rates file")

            return data

        except Exception:
            # если файл битый — пересоздаём
            with open(RATES_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_RATES, f, ensure_ascii=False, indent=2)

            return DEFAULT_RATES.copy()

    # ---------------------------
    # public
    # ---------------------------

    @classmethod
    def reload(cls):
        """
        Принудительная перезагрузка курсов (если отредактировали JSON)
        """
        cls._rates = None

    @classmethod
    def get_rates(cls) -> dict[str, float]:
        if cls._rates is None:
            cls._rates = cls._load_rates()
        return cls._rates

    @classmethod
    def to_rub(cls, amount: float, currency: str | None) -> int:
        """
        Конвертирует сумму в рубли
        """
        if amount <= 0:
            return 0

        currency = (currency or "RUB").upper()
        rates = cls.get_rates()

        rate = rates.get(currency, 1)
        return int(round(amount * rate))
