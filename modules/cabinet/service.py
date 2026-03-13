from modules.cabinet.models import load_config, save_config
from modules.tts.runtime import tts_runtime
from modules.utils.devices import clear_device_cache, list_output_devices


def get_api_key():
    config = load_config()
    return config.get("api_key", "")


def set_api_key(api_key: str):
    config = load_config()
    config["api_key"] = api_key.strip()
    save_config(config)


def get_audio_settings():
    config = load_config()
    return {
        "output_device": config.get("output_device", "")
    }


def set_output_device(device_name: str):
    config = load_config()
    config["output_device"] = device_name.strip()
    save_config(config)

    clear_device_cache()

    try:
        tts_runtime.reload_device()
    except Exception:
        pass


def get_output_devices():
    return list_output_devices()