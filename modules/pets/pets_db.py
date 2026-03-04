# modules/pets/pets_db.py
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class Pet:
    id: int
    name: str
    ws_show_cmd: str              # команда для вебсокета (показ/активация)
    ws_hide_cmd: str              # команда для скрытия
    display_seconds: int          # сколько секунд показывать (сколько живёт активный питомец)
    tick_value: int               # значение тика таймера (например 1 = реальное время)
    tick_enabled: bool            # применять ли tick_value
    donate_boost: float           # множитель буста донатов (например 1.0, 1.5, 2.0)
    donate_boost_enabled: bool    # применять ли donate_boost
    freeze_timer: bool            # заморозить таймер


class PetsDB:
    def __init__(self, db_path: str = "data/db/pets.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path.as_posix(), check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS pets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ws_show_cmd TEXT NOT NULL UNIQUE,
                    ws_hide_cmd TEXT NOT NULL,
                    display_seconds INTEGER NOT NULL DEFAULT 10,

                    tick_value INTEGER NOT NULL DEFAULT 1,
                    tick_enabled INTEGER NOT NULL DEFAULT 0,

                    donate_boost REAL NOT NULL DEFAULT 1.0,
                    donate_boost_enabled INTEGER NOT NULL DEFAULT 0,

                    freeze_timer INTEGER NOT NULL DEFAULT 0,

                    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
                );
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_pets_ws_show_cmd ON pets(ws_show_cmd);")

    # -------- CRUD --------

    def add_pet(
        self,
        name: str,
        ws_show_cmd: str,
        ws_hide_cmd: str,
        display_seconds: int = 10,
        tick_value: int = 1,
        tick_enabled: bool = False,
        donate_boost: float = 1.0,
        donate_boost_enabled: bool = False,
        freeze_timer: bool = False,
    ) -> int:
        with self._connect() as con:
            cur = con.execute("""
                INSERT INTO pets
                (name, ws_show_cmd, ws_hide_cmd, display_seconds,
                 tick_value, tick_enabled,
                 donate_boost, donate_boost_enabled,
                 freeze_timer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name.strip(),
                ws_show_cmd.strip(),
                ws_hide_cmd.strip(),
                int(display_seconds),
                int(tick_value),
                1 if tick_enabled else 0,
                float(donate_boost),
                1 if donate_boost_enabled else 0,
                1 if freeze_timer else 0,
            ))
            return int(cur.lastrowid)

    def delete_pet(self, pet_id: int) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM pets WHERE id = ?", (int(pet_id),))

    def get_all(self) -> List[Pet]:
        with self._connect() as con:
            rows = con.execute("SELECT * FROM pets ORDER BY id DESC").fetchall()
        return [self._row_to_pet(r) for r in rows]

    def get_by_id(self, pet_id: int) -> Optional[Pet]:
        with self._connect() as con:
            row = con.execute("SELECT * FROM pets WHERE id = ?", (int(pet_id),)).fetchone()
        return self._row_to_pet(row) if row else None

    def get_by_ws_show_cmd(self, ws_show_cmd: str) -> Optional[Pet]:
        with self._connect() as con:
            row = con.execute("SELECT * FROM pets WHERE ws_show_cmd = ?", (ws_show_cmd.strip(),)).fetchone()
        return self._row_to_pet(row) if row else None

    def update_pet(self, pet_id: int, **fields: Any) -> None:
        # простая утилита на будущее
        allowed = {
            "name", "ws_show_cmd", "ws_hide_cmd", "display_seconds",
            "tick_value", "tick_enabled",
            "donate_boost", "donate_boost_enabled",
            "freeze_timer"
        }
        updates: Dict[str, Any] = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return

        cols = []
        vals = []
        for k, v in updates.items():
            cols.append(f"{k} = ?")
            if k in ("tick_enabled", "donate_boost_enabled", "freeze_timer"):
                vals.append(1 if bool(v) else 0)
            elif k in ("display_seconds", "tick_value"):
                vals.append(int(v))
            elif k == "donate_boost":
                vals.append(float(v))
            else:
                vals.append(str(v).strip())

        vals.append(int(pet_id))
        with self._connect() as con:
            con.execute(f"UPDATE pets SET {', '.join(cols)} WHERE id = ?", tuple(vals))

    @staticmethod
    def _row_to_pet(r: sqlite3.Row) -> Pet:
        return Pet(
            id=int(r["id"]),
            name=str(r["name"]),
            ws_show_cmd=str(r["ws_show_cmd"]),
            ws_hide_cmd=str(r["ws_hide_cmd"]),
            display_seconds=int(r["display_seconds"]),
            tick_value=int(r["tick_value"]),
            tick_enabled=bool(r["tick_enabled"]),
            donate_boost=float(r["donate_boost"]),
            donate_boost_enabled=bool(r["donate_boost_enabled"]),
            freeze_timer=bool(r["freeze_timer"]),
        )

pets_db = PetsDB()