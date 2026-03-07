from .timer_service import TimerService
from .timer_state import timer_state
from modules.runtime.config_loader import ClientConfigLoader


def bootstrap_timer():
    tick = 1
    donate_boost = 1.0
    ws_url = ""
    try:
        config = ClientConfigLoader.load_timer_config()
        tick = config.get("default_tick", 1)
        donate_boost = config.get("default_donate_boost", 1.0)
        ws_url = config.get("ws_soket")
        print("[Timer] Config loaded")
    except Exception as e:
        print("[Timer] Config load failed:", e)


    TimerService.apply_pets(
        tick=tick,
        donate_boost=donate_boost
    )

    timer_state.ws_url = ws_url

    print(
        f"[Timer] config loaded tick={tick} donate_boost={donate_boost}"
    )

    print(
        f"[Timer] websocket: {ws_url}"
    )