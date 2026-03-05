import threading
import time

from modules.client.timer.timer_service import TimerService
from modules.utils.ws_client import send_ws_command

from .pet_state import pet_state


class PetService:

    # =========================================
    # INIT
    # =========================================

    @staticmethod
    def init_defaults(tick: int, donate_boost: float):

        pet_state.default_tick = tick
        pet_state.default_donate_boost = donate_boost

    # =========================================
    # START PET
    # =========================================

    @staticmethod
    def start_pet(pet: dict, ws_address: str):

        if not pet:
            return

        with pet_state.lock:

            # останавливаем предыдущего
            PetService._stop_current(ws_address)

            pet_state.stop_event.clear()

            thread = threading.Thread(
                target=PetService._pet_lifecycle,
                args=(pet, ws_address),
                daemon=True
            )

            pet_state.pet_thread = thread
            pet_state.active_pet = pet

            thread.start()

    # =========================================
    # STOP PET
    # =========================================

    @staticmethod
    def _stop_current(ws_address: str):

        if pet_state.active_pet:

            try:
                hide_cmd = pet_state.active_pet.get("ws_hide_cmd")

                if hide_cmd:
                    send_ws_command(hide_cmd, ws_address)

            except Exception as e:
                print(f"[Pet] hide error: {e}")

        pet_state.stop_event.set()

        pet_state.active_pet = None

        # вернуть дефолт таймера
        TimerService.apply_pets(
            pet_state.default_tick,
            pet_state.default_donate_boost
        )

    # =========================================
    # PET LIFECYCLE
    # =========================================

    @staticmethod
    def _pet_lifecycle(pet: dict, ws_address: str):

        delay = pet.get("delay_seconds", 0)
        duration = pet.get("display_seconds", 0)

        show_cmd = pet.get("ws_show_cmd")
        hide_cmd = pet.get("ws_hide_cmd")

        tick = pet.get("tick", 1)
        donate_boost = pet.get("donate_boost", 1.0)

        # delay before show

        if delay > 0:

            for _ in range(delay):

                if pet_state.stop_event.is_set():
                    return

                time.sleep(1)

        # show pet

        try:
            if show_cmd:
                send_ws_command(show_cmd, ws_address)
        except Exception as e:
            print(f"[Pet] show error: {e}")

        # применить настройки таймера

        TimerService.apply_pets(
            tick,
            donate_boost
        )

        # lifetime

        if duration > 0:

            for _ in range(duration):

                if pet_state.stop_event.is_set():
                    return

                time.sleep(1)

        # hide pet

        try:
            if hide_cmd:
                send_ws_command(hide_cmd, ws_address)
        except Exception as e:
            print(f"[Pet] hide error: {e}")

        # вернуть дефолт

        TimerService.apply_pets(
            pet_state.default_tick,
            pet_state.default_donate_boost
        )

        with pet_state.lock:
            pet_state.active_pet = None