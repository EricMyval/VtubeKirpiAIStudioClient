import sqlite3
import os
import json
from typing import List, Tuple, Optional


class WSStartEndDB:
    def __init__(self, db_path: str = "data/db/ws_start_end.db"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Создает директории и базу данных, если они не существуют"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица ws_start
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ws_start (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ws_command TEXT NOT NULL,
                time_sleep FLOAT NOT NULL,
                min_price INTEGER DEFAULT NULL,
                max_price INTEGER DEFAULT NULL,
                exclude_prices TEXT DEFAULT NULL,
                priority INTEGER DEFAULT 0,
                afk_enabled INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица ws_end
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ws_end (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ws_command TEXT NOT NULL,
                time_sleep FLOAT NOT NULL,
                min_price INTEGER DEFAULT NULL,
                max_price INTEGER DEFAULT NULL,
                exclude_prices TEXT DEFAULT NULL,
                priority INTEGER DEFAULT 0,
                afk_enabled INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self._ensure_column(conn, "ws_start", "afk_enabled")
        self._ensure_column(conn, "ws_end", "afk_enabled")

        conn.commit()
        conn.close()

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0"
            )
            conn.commit()

    def _check_condition(self, amount: int, min_price: Optional[int],
                         max_price: Optional[int], exclude_prices_json: Optional[str]) -> bool:
        """Проверяет условие для цены"""
        # Проверка минимума
        if min_price is not None and amount < min_price:
            return False

        # Проверка максимума
        if max_price is not None and amount > max_price:
            return False

        # Проверка исключений
        if exclude_prices_json:
            try:
                exclude_prices = json.loads(exclude_prices_json)
                if amount in exclude_prices:
                    return False
            except:
                pass  # Если JSON некорректный, игнорируем

        return True

    def get_start_commands(self, price: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ws_command, time_sleep, min_price, max_price, exclude_prices, afk_enabled
            FROM ws_start
            ORDER BY priority, created_at
        """)

        results = []
        for row in cursor.fetchall():
            ws_command, time_sleep, min_price, max_price, exclude_prices, afk_enabled = row

            if self._check_condition(price, min_price, max_price, exclude_prices):
                results.append(
                    (ws_command, time_sleep, bool(afk_enabled))
                )

        conn.close()
        return results

    def get_end_commands(self, price: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ws_command, time_sleep, min_price, max_price, exclude_prices, afk_enabled
            FROM ws_end
            ORDER BY priority, created_at
        """)

        results = []
        for row in cursor.fetchall():
            ws_command, time_sleep, min_price, max_price, exclude_prices, afk_enabled = row

            if self._check_condition(price, min_price, max_price, exclude_prices):
                results.append(
                    (ws_command, time_sleep, bool(afk_enabled))
                )

        conn.close()
        return results

    # CRUD операции для ws_start
    def add_start_command(
            self,
            ws_command: str,
            time_sleep: float,
            min_price: Optional[int] = None,
            max_price: Optional[int] = None,
            exclude_prices: Optional[List[int]] = None,
            priority: int = 0,
            afk_enabled: bool = False,
    ) -> int:
        """Добавляет команду в ws_start"""
        exclude_json = json.dumps(exclude_prices) if exclude_prices else None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ws_start (
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_prices,
                priority,
                afk_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ws_command,
            time_sleep,
            min_price,
            max_price,
            exclude_json,
            priority,
            1 if afk_enabled else 0
        ))

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return last_id

    def get_all_start_commands(self) -> List[Tuple]:
        """Возвращает все команды из ws_start отсортированные по приоритету"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id,
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_prices,
                priority,
                afk_enabled,
                created_at
            FROM ws_start
            ORDER BY priority, created_at
        ''')

        results = cursor.fetchall()
        conn.close()
        return results

    def delete_start_command(self, command_id: int) -> bool:
        """Удаляет команду из ws_start"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM ws_start WHERE id = ?', (command_id,))
        rows_affected = cursor.rowcount

        conn.commit()
        conn.close()
        return rows_affected > 0

    # CRUD операции для ws_end
    def add_end_command(
            self,
            ws_command: str,
            time_sleep: float,
            min_price: Optional[int] = None,
            max_price: Optional[int] = None,
            exclude_prices: Optional[List[int]] = None,
            priority: int = 0,
            afk_enabled: bool = False,
    ) -> int:
        """Добавляет команду в ws_end"""
        exclude_json = json.dumps(exclude_prices) if exclude_prices else None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ws_end (
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_prices,
                priority,
                afk_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ws_command,
            time_sleep,
            min_price,
            max_price,
            exclude_json,
            priority,
            1 if afk_enabled else 0
        ))

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return last_id

    def get_all_end_commands(self) -> List[Tuple]:
        """Возвращает все команды из ws_end отсортированные по приоритету"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id,
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_prices,
                priority,
                afk_enabled,
                created_at
            FROM ws_end
            ORDER BY priority, created_at
        ''')

        results = cursor.fetchall()
        conn.close()
        return results

    def delete_end_command(self, command_id: int) -> bool:
        """Удаляет команду из ws_end"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM ws_end WHERE id = ?', (command_id,))
        rows_affected = cursor.rowcount

        conn.commit()
        conn.close()
        return rows_affected > 0

    def update_start_command_priority(self, command_id: int, priority: int) -> bool:
        """Обновляет приоритет команды в ws_start"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE ws_start 
            SET priority = ?
            WHERE id = ?
        ''', (priority, command_id))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def update_end_command_priority(self, command_id: int, priority: int) -> bool:
        """Обновляет приоритет команды в ws_end"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE ws_end 
            SET priority = ?
            WHERE id = ?
        ''', (priority, command_id))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def get_start_command_by_id(self, command_id: int) -> Optional[Tuple]:
        """Получает команду start по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id,
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_prices,
                priority,
                afk_enabled
            FROM ws_start
            WHERE id = ?
        ''', (command_id,))

        result = cursor.fetchone()
        conn.close()
        return result

    def get_end_command_by_id(self, command_id: int) -> Optional[Tuple]:
        """Получает команду end по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id,
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_prices,
                priority,
                afk_enabled
            FROM ws_end
            WHERE id = ?
        ''', (command_id,))

        result = cursor.fetchone()
        conn.close()
        return result

    def update_start_command(
            self,
            command_id: int,
            ws_command: str,
            time_sleep: float,
            min_price: Optional[int] = None,
            max_price: Optional[int] = None,
            exclude_prices: Optional[List[int]] = None,
            priority: int = 0,
            afk_enabled: bool = False,
    ) -> bool:
        """Обновляет команду в ws_start"""
        exclude_json = json.dumps(exclude_prices) if exclude_prices else None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE ws_start
            SET
                ws_command = ?,
                time_sleep = ?,
                min_price = ?,
                max_price = ?,
                exclude_prices = ?,
                priority = ?,
                afk_enabled = ?
            WHERE id = ?
        ''', (
            ws_command,
            time_sleep,
            min_price,
            max_price,
            exclude_json,
            priority,
            1 if afk_enabled else 0,
            command_id
        ))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0

    def update_end_command(
            self,
            command_id: int,
            ws_command: str,
            time_sleep: float,
            min_price: Optional[int] = None,
            max_price: Optional[int] = None,
            exclude_prices: Optional[List[int]] = None,
            priority: int = 0,
            afk_enabled: bool = False,
    ) -> bool:
        """Обновляет команду в ws_end"""
        exclude_json = json.dumps(exclude_prices) if exclude_prices else None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE ws_end
            SET
                ws_command = ?,
                time_sleep = ?,
                min_price = ?,
                max_price = ?,
                exclude_prices = ?,
                priority = ?,
                afk_enabled = ?
            WHERE id = ?
        ''', (
            ws_command,
            time_sleep,
            min_price,
            max_price,
            exclude_json,
            priority,
            1 if afk_enabled else 0,
            command_id
        ))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0
