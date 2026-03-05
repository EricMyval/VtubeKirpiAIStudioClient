from modules.client.timer.timer_state import timer_state
from .pet_service import PetService


def handle_pet(event: dict, ws_address: str):

    pet = event.get("pet")

    if not pet:
        return

    PetService.start_pet(
        pet,
        ws_address
    )


def init_pet_defaults():

    PetService.init_defaults(
        timer_state.tick,
        timer_state.donate_boost
    )