# modules/pets/pets_manager.py
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from modules.pets.pets_db import PetsDB, Pet, pets_db
from modules.timer.timer import timer
from modules.web_sockets.sender import send_ws_command

@dataclass
class ActivePet:
    pet: Pet
    activated_at: float
    expires_at: float  # unix time


class PetsManager:
    DEF_PATH = Path("data/db/pets_def.json")
    DEF_FALLBACK = {"donate_boost": 1.0, "tick": 1, "freeze": False}

    def __init__(self, db: PetsDB, timer):
        self._db = db
        self._timer = timer
        self._lock = threading.RLock()
        self._active: Optional[ActivePet] = None

        self._wake_event = threading.Event()
        self._stop_event = threading.Event()

        # кеш дефолтов, чтобы не читать файл каждую секунду
        self._defaults_cache = self._load_defaults_from_file()

        self._watcher_thread = threading.Thread(
            target=self._watcher_loop,
            name="PetsManagerWatcher",
            daemon=True,
        )
        self._watcher_thread.start()

    # ---------- defaults (pets_def.json) ----------

    def _normalize_defaults(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        d = dict(self.DEF_FALLBACK)

        if isinstance(raw, dict):
            if "donate_boost" in raw:
                try:
                    d["donate_boost"] = float(raw["donate_boost"])
                except Exception:
                    pass
            if "tick" in raw:
                try:
                    d["tick"] = int(raw["tick"])
                except Exception:
                    pass
            if "freeze" in raw:
                d["freeze"] = bool(raw["freeze"])

        # защита от поломок таймера
        if d["tick"] == 0:
            d["tick"] = 1
        if d["donate_boost"] <= 0:
            d["donate_boost"] = 1.0

        return d

    def _load_defaults_from_file(self) -> Dict[str, Any]:
        self.DEF_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not self.DEF_PATH.exists():
            self.DEF_PATH.write_text(
                json.dumps(self.DEF_FALLBACK, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            return dict(self.DEF_FALLBACK)

        try:
            raw = json.loads(self.DEF_PATH.read_text(encoding="utf-8"))
            normalized = self._normalize_defaults(raw)
            # если файл кривой — поправим
            if not isinstance(raw, dict) or normalized != raw:
                self.DEF_PATH.write_text(
                    json.dumps(normalized, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            return normalized
        except Exception:
            # битый json — восстановим
            self.DEF_PATH.write_text(
                json.dumps(self.DEF_FALLBACK, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            return dict(self.DEF_FALLBACK)

    def get_defaults(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._defaults_cache)

    def save_defaults(self, donate_boost: float, tick: int, freeze: bool) -> Dict[str, Any]:
        new_def = self._normalize_defaults({
            "donate_boost": donate_boost,
            "tick": tick,
            "freeze": freeze,
        })
        with self._lock:
            self._defaults_cache = dict(new_def)
            self.DEF_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.DEF_PATH.write_text(json.dumps(new_def, ensure_ascii=False, indent=2), encoding="utf-8")
        return new_def

    # ---------- публичные методы ----------

    def stop(self) -> None:
        self._stop_event.set()
        self._wake_event.set()

    def trigger_by_ws_command(self, ws_show_cmd: str) -> bool:
        ws_show_cmd = (ws_show_cmd or "").strip()
        if not ws_show_cmd:
            return False

        pet = self._db.get_by_ws_show_cmd(ws_show_cmd)
        if not pet:
            return False

        now = time.time()
        expires_at = now + max(1, int(pet.display_seconds))

        with self._lock:
            if self._active is not None:
                self._send_ws(self._active.pet.ws_hide_cmd)

            self._active = ActivePet(
                pet=pet,
                activated_at=now,
                expires_at=expires_at,
            )

            influence = self.get_timer_influence()
            self._timer.apply_pets_influence(influence)

            self._wake_event.set()

        return True

    def force_hide_active(self) -> None:
        with self._lock:
            if not self._active:
                return
            pet_to_hide = self._active.pet
            self._active = None
            self._wake_event.set()

        self._send_ws(pet_to_hide.ws_hide_cmd, note="force hide")
        self._timer.apply_pets_influence(self.get_timer_influence())

        print("[PetsManager] active pet hidden (force)")

    def get_active_name_and_remaining(self):
        with self._lock:
            if not self._active:
                return None, 0
            now = time.time()
            remaining = int(max(0, self._active.expires_at - now))
            return self._active.pet.name, remaining

    def get_timer_influence(self) -> Dict[str, Any]:
        """
        Логика влияния на таймер:

        - Если НЕТ активного пета:
            • donate_boost = defaults.donate_boost
            • tick = defaults.tick
            • freeze = False   (ВАЖНО: таймер никогда не заморожен без пета)

        - Если пет АКТИВЕН:
            • tick:
                - pet.tick_value, если pet.tick_enabled
                - иначе defaults.tick
            • donate_boost:
                - pet.donate_boost, если pet.donate_boost_enabled
                - иначе defaults.donate_boost
            • freeze:
                - True ТОЛЬКО если pet.freeze_timer == True
                - defaults.freeze ИГНОРИРУЕТСЯ
        """
        with self._lock:
            defaults = dict(self._defaults_cache)

            # --- НЕТ ПЕТА: таймер ВСЕГДА идёт ---
            if not self._active:
                tick = int(defaults.get("tick", 1))
                donate_boost = float(defaults.get("donate_boost", 1.0))

                # защита
                if tick == 0:
                    tick = 1
                if donate_boost <= 0:
                    donate_boost = 1.0

                return {
                    "donate_boost": donate_boost,
                    "tick": tick,
                    "freeze": False,
                }

            # --- ЕСТЬ АКТИВНЫЙ ПЕТ ---
            pet = self._active.pet

            tick = (
                int(pet.tick_value)
                if pet.tick_enabled
                else int(defaults.get("tick", 1))
            )

            donate_boost = (
                float(pet.donate_boost)
                if pet.donate_boost_enabled
                else float(defaults.get("donate_boost", 1.0))
            )

            freeze = bool(pet.freeze_timer)

            # защита
            if tick == 0:
                tick = 1
            if donate_boost <= 0:
                donate_boost = 1.0

            return {
                "donate_boost": donate_boost,
                "tick": tick,
                "freeze": freeze,
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Полный статус (для UI мониторинга). Возвращает JSON-friendly dict.
        + defaults (чтобы фронт не хардкодил 1/1/false)
        """
        with self._lock:
            defaults = dict(self._defaults_cache)

            if not self._active:
                return {
                    "active": False,
                    "active_name": None,
                    "remaining": 0,
                    "expires_at": 0,
                    "activated_at": 0,
                    "defaults": defaults,
                    "influence": defaults,
                    "pet": None,
                }

            now = time.time()
            remaining = int(max(0, self._active.expires_at - now))
            pet = self._active.pet
            influence = self.get_timer_influence()

            if remaining <= 0:
                self._wake_event.set()

            return {
                "active": True,
                "active_name": pet.name,
                "remaining": remaining,
                "expires_at": int(self._active.expires_at),
                "activated_at": int(self._active.activated_at),
                "defaults": defaults,
                "influence": influence,
                "pet": {
                    "id": pet.id,
                    "name": pet.name,
                    "ws_show_cmd": pet.ws_show_cmd,
                    "ws_hide_cmd": pet.ws_hide_cmd,
                    "display_seconds": pet.display_seconds,
                    "tick_value": pet.tick_value,
                    "tick_enabled": bool(pet.tick_enabled),
                    "donate_boost": float(pet.donate_boost),
                    "donate_boost_enabled": bool(pet.donate_boost_enabled),
                    "freeze_timer": bool(pet.freeze_timer),
                },
            }

    # ---------- авто-hide поток ----------

    def _watcher_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                active = self._active
                if not active:
                    wait_seconds = None
                else:
                    wait_seconds = max(0.0, active.expires_at - time.time())

            if wait_seconds is None:
                self._wake_event.wait(timeout=3)
                self._wake_event.clear()
                continue

            triggered = self._wake_event.wait(timeout=wait_seconds)
            self._wake_event.clear()

            if triggered:
                continue

            with self._lock:
                if not self._active:
                    continue
                if time.time() < self._active.expires_at:
                    continue
                pet_to_hide = self._active.pet
                self._active = None

            self._timer.apply_pets_influence(self.get_timer_influence())
            self._send_ws(pet_to_hide.ws_hide_cmd, note="auto hide (expired)")
            print(f"[PetsManager] pet expired and hidden id={pet_to_hide.id} name={pet_to_hide.name!r}")


    def _send_ws(self, command: str, note: str = "") -> None:
        cmd = (command or "").strip()
        if not cmd:
            print(f"[PetsManager][WS] EMPTY_CMD note={note!r}")
            return
        send_ws_command(cmd)
        if note:
            print(f"[PetsManager][WS] sent: {cmd} | {note}")
        else:
            print(f"[PetsManager][WS] sent: {cmd}")

pets_manager = PetsManager(pets_db, timer)