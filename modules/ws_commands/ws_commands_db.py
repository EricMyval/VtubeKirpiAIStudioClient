import sqlite3
import os
from typing import List, Tuple, Optional


class WSCommandsDB:
    def __init__(self, db_path: str = "data/db/ws_commands.db"):
        self.db_path = db_path
        self._ensure_db_exists()
        self._upgrade_db_structure()

    def _ensure_db_exists(self) -> None:
        """Создает директории и базу данных, если они не существуют"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ws_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ws_price INTEGER NOT NULL,
                ws_command TEXT NOT NULL,
                ws_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def _upgrade_db_structure(self) -> None:
        """Обновляет структуру базы данных, добавляя поле delay_seconds если его нет"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Проверяем, существует ли поле delay_seconds
        cursor.execute("PRAGMA table_info(ws_commands)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'delay_seconds' not in columns:
            # Добавляем новое поле со значением по умолчанию 30 секунд
            cursor.execute('''
                ALTER TABLE ws_commands 
                ADD COLUMN delay_seconds INTEGER DEFAULT 30
            ''')
            print("База данных обновлена: добавлено поле delay_seconds со значением по умолчанию 30")

        conn.commit()
        conn.close()

    def add_command(self, price: int, command: str, text: str, delay_seconds: int = 30) -> int:
        """Добавляет новую команду в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ws_commands (ws_price, ws_command, ws_text, delay_seconds)
            VALUES (?, ?, ?, ?)
        ''', (price, command, text, delay_seconds))

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return last_id

    def delete_command(self, command_id: int) -> bool:
        """Удаляет команду по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM ws_commands WHERE id = ?', (command_id,))
        rows_affected = cursor.rowcount

        conn.commit()
        conn.close()

        return rows_affected > 0

    def update_command(self, command_id: int, price: int, command: str, text: str,
                       delay_seconds: int = 30) -> bool:
        """Обновляет существующую команду"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE ws_commands 
            SET ws_price = ?, ws_command = ?, ws_text = ?, delay_seconds = ?
            WHERE id = ?
        ''', (price, command, text, delay_seconds, command_id))

        rows_affected = cursor.rowcount

        conn.commit()
        conn.close()

        return rows_affected > 0

    def get_all_commands(self) -> List[Tuple]:
        """Возвращает все команды, отсортированные по цене"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, ws_price, ws_command, ws_text, delay_seconds, created_at
            FROM ws_commands 
            ORDER BY ws_price
        ''')

        results = cursor.fetchall()
        conn.close()

        return results

    def get_command_by_id(self, command_id: int) -> Optional[Tuple]:
        """Возвращает команду по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, ws_price, ws_command, ws_text, delay_seconds, created_at
            FROM ws_commands 
            WHERE id = ?
        ''', (command_id,))

        result = cursor.fetchone()
        conn.close()

        return result

    def search_commands(self, search_term: str) -> List[Tuple]:
        """Поиск команд по тексту или команде"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        search_pattern = f'%{search_term}%'
        cursor.execute('''
            SELECT id, ws_price, ws_command, ws_text, delay_seconds, created_at
            FROM ws_commands 
            WHERE ws_command LIKE ? OR ws_text LIKE ?
            ORDER BY ws_price
        ''', (search_pattern, search_pattern))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_command_by_price(self, price: int) -> List[Tuple[str, int]]:
        """Возвращает список команд по цене с их задержками"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ws_command, delay_seconds FROM ws_commands 
            WHERE ws_price = ?
            ORDER BY id
        ''', (price,))

        results = cursor.fetchall()
        conn.close()

        return results if results else []

    def get_text_by_price(self, price: int) -> str:
        """Возвращает объединенный текст по цене"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ws_text FROM ws_commands 
            WHERE ws_price = ? AND ws_text IS NOT NULL AND ws_text != ''
            ORDER BY id
        ''', (price,))

        results = cursor.fetchall()
        conn.close()

        if not results:
            return ""

        texts = [result[0] for result in results]
        return " ".join(texts)

    # ==========================
    # Дополнительная фраза в конце (Управление командами)
    # ==========================

    def add_text_by_price(self, message, amount) -> str:
        if message and message[-1] not in {'.', '!', '?'}:
            return f"{message}. {self.get_text_by_price(int(float(amount)))}"
        else:
            return f"{message} {self.get_text_by_price(int(float(amount)))}"

    def update_delay(self, command_id: int, delay_seconds: int) -> bool:
        """Обновляет только задержку для команды"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE ws_commands 
            SET delay_seconds = ?
            WHERE id = ?
        ''', (delay_seconds, command_id))

        rows_affected = cursor.rowcount

        conn.commit()
        conn.close()

        return rows_affected > 0

    def get_delay_by_command_id(self, command_id: int) -> Optional[int]:
        """Возвращает задержку для команды по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT delay_seconds FROM ws_commands 
            WHERE id = ?
        ''', (command_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

ws_db = WSCommandsDB()