# modules/donation/donation_monitor.py
import time
import threading
import sqlite3
from typing import Callable, Optional, Tuple
from pathlib import Path

class DonationDB:
    """Класс для работы с базой данных донатов"""
    def __init__(self, db_path: str = 'data/db/donate.db'):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS donations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    message TEXT,
                    amount_user TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def _get_connection(self) -> sqlite3.Connection:
        """Создает новое соединение с базой данных"""
        return sqlite3.connect(self.db_path)

    def add_donate(self, user: str, message: str, amount_user: str):
        """Добавляет донат в базу данных"""
        with self._get_connection() as conn:
            conn.execute(
                'INSERT INTO donations (user, message, amount_user) VALUES (?, ?, ?)',
                (user, message, amount_user)
            )
    def count_donations(self) -> int:
        """Возвращает количество донатов в очереди"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM donations")
            return cursor.fetchone()[0]

    def get_oldest_donate(self) -> Optional[Tuple[str, str, str]]:
        """Возвращает самый старый донат"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user, message, amount_user FROM donations
                ORDER BY timestamp ASC
                LIMIT 1
            ''')
            return cursor.fetchone()

    def delete_oldest_donate(self):
        """Удаляет самый старый донат"""
        with self._get_connection() as conn:
            conn.execute('''
                DELETE FROM donations
                WHERE id = (
                    SELECT id FROM donations
                    ORDER BY timestamp ASC
                    LIMIT 1
                )
            ''')

class DonationMonitor:
    """Класс для мониторинга и обработки донатов"""
    def __init__(
            self,
            poll_interval: float = 1.0
    ):
        self.db = DonationDB('data/db/donate.db')
        self.execute_donation = None
        self.poll_interval = poll_interval
        self._running = False
        self._thread = None

    def set_execute_donation(self, execute_donation: Optional[Callable[[str, str, str], None]]):
        self.execute_donation = execute_donation
        self.start()

    def _process_donations(self):
        """Основной цикл обработки донатов"""
        while self._running:
            try:
                donation = self.db.get_oldest_donate()
                if donation is not None:
                    user, message, amount_user = donation
                    self.db.delete_oldest_donate()
                    if self.execute_donation:
                        self.execute_donation(user, message, amount_user)
            except Exception as e:
                print(f"Ошибка при обработке доната: {e}")
            time.sleep(self.poll_interval)

    def start(self):
        """Запускает мониторинг донатов"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._process_donations, daemon=True)
        self._thread.start()

    def stop(self):
        """Останавливает мониторинг донатов"""
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера"""
        self.stop()

donation_monitor = DonationMonitor()