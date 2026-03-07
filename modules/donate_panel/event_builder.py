def build_donate_event(username, amount, message):

    return {

        "platform": "manual",

        "user": username,
        "username": username,

        "amount": amount,
        "message": message,

        "formatted_text": message,

        "voice_file_path": None,
        "voice_reference_text": None,

        "image_url": None,

        "start_commands": [],
        "ws_commands": [],
        "end_commands": [],

        "alert": None
    }