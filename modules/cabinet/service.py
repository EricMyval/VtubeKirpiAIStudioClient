from .models import load_config, save_config


def get_api_key():
    config = load_config()
    return config.get("api_key", "")


def set_api_key(api_key: str):
    config = load_config()
    config["api_key"] = api_key.strip()
    save_config(config)