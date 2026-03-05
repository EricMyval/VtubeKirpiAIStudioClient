import asyncio
import threading

from modules.client.runtime.ws_client import send_ws_command_async
from .timer_state import timer_state


def send_ws_command(message: str) -> None:

    if not timer_state.ws_url:
        print("[Timer] WS url not set")
        return

    # защита от дублей
    with timer_state.ws_lock:
        if message == timer_state.last_payload:
            return

        timer_state.last_payload = message

    def runner():
        try:
            asyncio.run(
                send_ws_command_async(
                    message,
                    timer_state.ws_url
                )
            )
        except Exception as e:
            print(f"[Timer][WebSocket ERROR]: {e}")

    threading.Thread(
        target=runner,
        daemon=True
    ).start()


def emit_time(formatted_time: str) -> None:

    send_ws_command(
        f'{{"action":"timer","data":"{formatted_time}"}}'
    )