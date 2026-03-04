import sqlite3
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any


# =======================
# Models
# =======================

@dataclass
class AwardItem:
    id: int
    award_name: str
    team_name: str
    delay_seconds: int
    display_type: int  # 1=ИИ, 2=озвучка текста, 3=без озвучки
    award_text: str    # <-- НОВОЕ ПОЛЕ
    is_group: int = 0  # 1=группа (рандом из списка наград)


# =======================
# DB
# =======================

class AwardsDB:
    """
    SQLite база: data/db/awards.db

    Таблица awards:
      - award_name (str)
      - team_name (str)
      - delay_seconds (int)
      - display_type (int: 1/2/3)
      - award_text (str)
      - is_group (int: 0/1)

    Таблица award_group_items:
      - parent_id (int) -> awards.id (группа)
      - child_id (int)  -> awards.id (элемент)
    """

    def __init__(self, db_path: str = "data/db/awards.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path.as_posix(), check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con

    # =======================
    # Normalizers
    # =======================

    @staticmethod
    def _normalize_display_type(v: Any) -> int:
        try:
            iv = int(v)
        except Exception:
            return 3
        return iv if iv in (1, 2, 3) else 3

    @staticmethod
    def _normalize_delay(v: Any) -> int:
        try:
            iv = int(v)
        except Exception:
            return 0
        return max(0, iv)

    @staticmethod
    def _normalize_is_group(v: Any) -> int:
        if v in (True, 1, "1", "on", "true", "True", "yes", "y"):
            return 1
        return 0

    @staticmethod
    def _normalize_text(v: Any) -> str:
        return (v or "").strip()

    # =======================
    # Init / Migration
    # =======================

    def _has_column(self, con: sqlite3.Connection, table: str, col: str) -> bool:
        rows = con.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == col for r in rows)

    def _init_db(self) -> None:
        with self._connect() as con:
            # основная таблица
            con.execute("""
                CREATE TABLE IF NOT EXISTS awards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    award_name TEXT NOT NULL,
                    team_name TEXT NOT NULL,
                    delay_seconds INTEGER NOT NULL DEFAULT 0,
                    display_type INTEGER NOT NULL DEFAULT 3 CHECK(display_type IN (1,2,3)),
                    award_text TEXT NOT NULL DEFAULT ''
                )
            """)

            # миграции
            if not self._has_column(con, "awards", "is_group"):
                con.execute(
                    "ALTER TABLE awards ADD COLUMN is_group INTEGER NOT NULL DEFAULT 0"
                )

            if not self._has_column(con, "awards", "award_text"):
                con.execute(
                    "ALTER TABLE awards ADD COLUMN award_text TEXT NOT NULL DEFAULT ''"
                )

            # таблица связей группы
            con.execute("""
                CREATE TABLE IF NOT EXISTS award_group_items (
                    parent_id INTEGER NOT NULL,
                    child_id INTEGER NOT NULL,
                    PRIMARY KEY (parent_id, child_id),
                    FOREIGN KEY(parent_id) REFERENCES awards(id) ON DELETE CASCADE,
                    FOREIGN KEY(child_id) REFERENCES awards(id) ON DELETE CASCADE
                )
            """)

            # индексы
            con.execute("CREATE INDEX IF NOT EXISTS idx_awards_award_name ON awards(award_name)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_awards_team_name ON awards(team_name)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_awards_is_group ON awards(is_group)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_award_group_parent ON award_group_items(parent_id)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_award_group_child ON award_group_items(child_id)")

            con.commit()

    # =======================
    # CRUD
    # =======================

    def list_all(self) -> List[AwardItem]:
        with self._connect() as con:
            rows = con.execute("""
                SELECT id, award_name, team_name,
                       delay_seconds, display_type,
                       award_text, is_group
                FROM awards
                ORDER BY id DESC
            """).fetchall()
        return [AwardItem(**dict(r)) for r in rows]

    def get(self, item_id: int) -> Optional[AwardItem]:
        with self._connect() as con:
            row = con.execute("""
                SELECT id, award_name, team_name,
                       delay_seconds, display_type,
                       award_text, is_group
                FROM awards
                WHERE id=?
            """, (item_id,)).fetchone()
        return AwardItem(**dict(row)) if row else None

    def get_by_award_name(self, award_name: str) -> Optional[AwardItem]:
        award_name = (award_name or "").strip()
        if not award_name:
            return None

        with self._connect() as con:
            row = con.execute("""
                SELECT id, award_name, team_name,
                       delay_seconds, display_type,
                       award_text, is_group
                FROM awards
                WHERE award_name=?
                ORDER BY id DESC
                LIMIT 1
            """, (award_name,)).fetchone()
        return AwardItem(**dict(row)) if row else None

    def create(
        self,
        award_name: str,
        team_name: str,
        delay_seconds: int = 0,
        display_type: int = 3,
        award_text: str = "",
        is_group: int = 0,
    ) -> int:
        award_name = (award_name or "").strip()
        team_name = (team_name or "").strip()
        if not award_name or not team_name:
            raise ValueError("award_name и team_name обязательны")

        delay_seconds = self._normalize_delay(delay_seconds)
        display_type = self._normalize_display_type(display_type)
        award_text = self._normalize_text(award_text)
        is_group = self._normalize_is_group(is_group)

        with self._connect() as con:
            cur = con.execute("""
                INSERT INTO awards
                    (award_name, team_name, delay_seconds, display_type, award_text, is_group)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                award_name,
                team_name,
                delay_seconds,
                display_type,
                award_text,
                is_group,
            ))
            con.commit()
            return int(cur.lastrowid)

    def update(
        self,
        item_id: int,
        award_name: str,
        team_name: str,
        delay_seconds: int,
        display_type: int,
        award_text: str,
        is_group: int,
    ) -> None:
        award_name = (award_name or "").strip()
        team_name = (team_name or "").strip()
        if not award_name or not team_name:
            raise ValueError("award_name и team_name обязательны")

        delay_seconds = self._normalize_delay(delay_seconds)
        display_type = self._normalize_display_type(display_type)
        award_text = self._normalize_text(award_text)
        is_group = self._normalize_is_group(is_group)

        with self._connect() as con:
            con.execute("""
                UPDATE awards
                SET award_name=?,
                    team_name=?,
                    delay_seconds=?,
                    display_type=?,
                    award_text=?,
                    is_group=?
                WHERE id=?
            """, (
                award_name,
                team_name,
                delay_seconds,
                display_type,
                award_text,
                is_group,
                item_id,
            ))
            con.commit()

    def delete(self, item_id: int) -> None:
        with self._connect() as con:
            con.execute(
                "DELETE FROM award_group_items WHERE parent_id=? OR child_id=?",
                (item_id, item_id),
            )
            con.execute("DELETE FROM awards WHERE id=?", (item_id,))
            con.commit()

    # =======================
    # Groups
    # =======================

    def get_children_ids(self, parent_id: int) -> List[int]:
        with self._connect() as con:
            rows = con.execute("""
                SELECT child_id
                FROM award_group_items
                WHERE parent_id=?
                ORDER BY child_id ASC
            """, (parent_id,)).fetchall()
        return [int(r["child_id"]) for r in rows]

    def set_children(self, parent_id: int, child_ids: List[int]) -> None:
        uniq: List[int] = []
        seen = set()

        for x in child_ids or []:
            try:
                ix = int(x)
            except Exception:
                continue
            if ix <= 0 or ix == parent_id or ix in seen:
                continue
            seen.add(ix)
            uniq.append(ix)

        with self._connect() as con:
            con.execute("DELETE FROM award_group_items WHERE parent_id=?", (parent_id,))
            if uniq:
                con.executemany(
                    "INSERT OR IGNORE INTO award_group_items(parent_id, child_id) VALUES (?, ?)",
                    [(parent_id, cid) for cid in uniq],
                )
            con.commit()

    def resolve_random_award(self, item: AwardItem, max_depth: int = 5) -> Optional[AwardItem]:
        if not item or not item.is_group:
            return item

        current = item
        for _ in range(max_depth):
            children = self.get_children_ids(current.id)
            if not children:
                return None

            chosen = self.get(random.choice(children))
            if not chosen:
                continue

            if chosen.is_group:
                current = chosen
                continue

            return chosen

        return None

    # =======================
    # Helpers for UI
    # =======================

    def list_all_with_children_names(self) -> List[Dict[str, Any]]:
        items = self.list_all()

        with self._connect() as con:
            rows = con.execute("""
                SELECT gi.parent_id,
                       a.id AS child_id,
                       a.award_name AS child_name
                FROM award_group_items gi
                JOIN awards a ON a.id = gi.child_id
                ORDER BY gi.parent_id DESC, a.id ASC
            """).fetchall()

        children_map: Dict[int, List[Dict[str, Any]]] = {}
        for r in rows:
            pid = int(r["parent_id"])
            children_map.setdefault(pid, []).append(
                {"id": int(r["child_id"]), "award_name": r["child_name"]}
            )

        return [
            {"item": it, "children": children_map.get(it.id, [])}
            for it in items
        ]

    # =======================
    # Form upsert
    # =======================

    def upsert_from_form(self, form: Dict[str, Any]) -> int:
        raw_id = (form.get("id") or "").strip()

        award_name = form.get("award_name")
        team_name = form.get("team_name")
        delay_seconds = form.get("delay_seconds")
        display_type = form.get("display_type")
        award_text = form.get("award_text")
        is_group = form.get("is_group")

        child_ids: List[int] = []
        if hasattr(form, "getlist"):
            child_ids = form.getlist("group_children")  # type: ignore
        else:
            raw = form.get("group_children") or ""
            if isinstance(raw, str) and raw.strip():
                child_ids = [x.strip() for x in raw.split(",")]

        if raw_id:
            item_id = int(raw_id)
            self.update(
                item_id,
                award_name,
                team_name,
                delay_seconds,
                display_type,
                award_text,
                is_group,
            )
        else:
            item_id = self.create(
                award_name,
                team_name,
                delay_seconds,
                display_type,
                award_text,
                is_group,
            )

        saved = self.get(item_id)
        if saved and saved.is_group:
            self.set_children(item_id, child_ids)
        else:
            self.set_children(item_id, [])

        return item_id

awards_db = AwardsDB()