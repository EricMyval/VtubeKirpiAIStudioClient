import json
from modules.utils.ws_client import send_ws_command

def show_message_image(image_url: str, ws_url: str):
    if image_url:
        payload = json.dumps({
            "action": "donate_image_show",
            "data": image_url
        })
        send_ws_command(payload, ws_url)


def hide_message_image(ws_url: str):
    payload = json.dumps({
        "action": "donate_image_hide",
        "data": "none"
    })
    send_ws_command(payload, ws_url)