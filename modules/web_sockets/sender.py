import websocket
import websockets
from modules.config.config import cfg

def send_ws_command(command: str):
    try:
        url = cfg.get_websocket_config().get("address", "ws://127.0.0.1:19190/")
        ws = websocket.create_connection(url)
        ws.send(command)
        ws.close()
        print(f"📡 WebSocket отправлен: {command}")
    except Exception as e:
        print(f"[Ошибка WebSocket]: {command} - {e}")

async def send_ws_command_async(command: str) -> None:
    url = cfg.get_websocket_config().get("address", "ws://127.0.0.1:19190/")
    try:
        async with websockets.connect(url) as ws:
            await ws.send(command)
            print(f"📡 WebSocket отправлен: {command}")
    except Exception as e:
        print(f"[Ошибка WebSocket]: {command} - {e}")