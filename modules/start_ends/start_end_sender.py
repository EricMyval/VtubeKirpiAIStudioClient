import time
from modules.afk.afk_state import afk_state, send_ws_command
from modules.phrases.phrases import format_command_template
from modules.web_admin.pages.ws_start_end import start_end_db

def execute_start_commands(price: int, user: str = "", message: str = ""):
    if price < 0:
        price = 0
    afk_on = afk_state.is_enabled()
    commands = start_end_db.get_start_commands(price)
    for command, sleep_time, afk_only in commands:
        if afk_on != afk_only:
            continue
        formatted_command = format_command_template(command, price, user, message)
        send_ws_command(formatted_command)
        if sleep_time > 0:
            time.sleep(sleep_time)

def execute_end_commands(price: int, user: str = "", message: str = ""):
    if price < 0:
        price = 0
    afk_on = afk_state.is_enabled()
    commands = start_end_db.get_end_commands(price)
    for command, sleep_time, afk_only in commands:
        if afk_on != afk_only:
            continue
        formatted_command = format_command_template(command, price, user, message)
        send_ws_command(formatted_command)
        if sleep_time > 0:
            time.sleep(sleep_time)