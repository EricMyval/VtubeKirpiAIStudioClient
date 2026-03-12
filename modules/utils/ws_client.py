import websocket
import websockets
import time

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

def send_command_list(commands, ws_address):
    if ws_address:
        for cmd in commands:
            command_text = cmd.get("command")
            delay = cmd.get("delay", 0)
            if command_text:
                send_ws_command(command_text, ws_address)
            if delay and delay > 0:
                end_time = time.time() + delay
                while time.time() < end_time:
                    time.sleep(0.1)