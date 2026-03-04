# modules/client/audio/service.py

from .models import load_config, save_config
from .devices import list_output_devices, clear_device_cache


def get_audio_settings():
    return load_config()


def set_output_device(device_name: str):
    config = load_config()
    config["output_device"] = device_name.strip()
    save_config(config)
    clear_device_cache()


def get_output_devices():
    return list_output_devices()