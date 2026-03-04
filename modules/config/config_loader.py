from pathlib import Path
import yaml
from typing import Dict, Any

DEFAULT_CONFIG = {
    "audio": {
        "output_device": "CABLE Input",
        "alternative_devices": ["Output (VB-Audio Point)"]
    },
    "websocket": {
        "address": "ws://127.0.0.1:19190/"
    },
    "donation": {
        "ai_min": 90,
        "ai_max": 90
    }
}

class Config:
    def __init__(self, path: str = "data/config/config.yaml"):
        """
        Инициализация конфигурации.

        Args:
            path (str): Путь к файлу конфигурации. По умолчанию 'data/config/config.yaml'.
        """
        self.path = Path(path)
        self._ensure_exists()
        self._data = self._load()

    def reload(self):
        self._data = self._load()

    def _ensure_exists(self) -> None:
        """Создает файл конфигурации с дефолтными значениями, если он не существует."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULT_CONFIG)

    def _load(self) -> Dict[str, Any]:
        """Загружает конфигурацию из YAML файла."""
        with open(self.path, "r", encoding="utf-8") as f:
            loaded_config = yaml.safe_load(f) or {}
            # Мердж с дефолтными значениями (глубокое слияние)
            merged_config = self._deep_merge(DEFAULT_CONFIG.copy(), loaded_config)
            return merged_config

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Рекурсивное глубокое слияние словарей."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def save(self, data: Dict[str, Any]) -> None:
        """
        Сохраняет конфигурацию в YAML файл.

        Args:
            data (dict): Словарь с данными конфигурации.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        self._data = data

    @property
    def data(self) -> Dict[str, Any]:
        """Возвращает полную конфигурацию."""
        return self._data

    def update(self, **kwargs) -> None:
        """
        Обновляет конфигурацию.

        Args:
            **kwargs: Ключи и значения для обновления.
        """
        new_data = dict(self._data)
        new_data.update(kwargs)
        self.save(new_data)

    def get_audio_config(self):
        return self.data.get("audio", {})

    def update_audio_config(self, output_device: str, alternatives: list = None):
        audio_config = self.get_audio_config()
        audio_config["output_device"] = output_device
        if alternatives:
            audio_config["alternative_devices"] = alternatives
        self.update(audio=audio_config)

    def get_websocket_config(self):
        return self.data.get("websocket", {})

    def update_websocket_config(self, address: str):
        websocket_config = self.get_websocket_config()
        websocket_config["address"] = address
        self.update(websocket=websocket_config)

    def get_donation_config(self):
        """Возвращает конфигурацию донатов"""
        return self.data.get("donation", {})

    def update_donation_config(self,
                                ai_donation_min: int = 90,
                                ai_donation_max: int = 90):
        """Обновляет конфигурацию донатов"""
        donation_config = self.get_donation_config()
        donation_config["ai_min"] = ai_donation_min
        donation_config["ai_max"] = ai_donation_max
        self.update(donation=donation_config)