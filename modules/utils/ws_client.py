import websocket
import websockets

def send_ws_command(command: str, url: str):
    try:
        ws = websocket.create_connection(url)
        ws.send(command)
        ws.close()
        print(f"📡 WebSocket отправлен: {command}")
    except Exception as e:
        print(f"[Ошибка WebSocket]: {command} - {e}")

async def send_ws_command_async(command: str, url: str) -> None:
    try:
        async with websockets.connect(url) as ws:
            await ws.send(command)
            print(f"📡 WebSocket отправлен: {command}")
    except Exception as e:
        print(f"[Ошибка WebSocket]: {command} - {e}")