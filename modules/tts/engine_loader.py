import subprocess
import time
import json
import socket
import os

from modules.tts.config import get_tts_config
from modules.tts.voice_vibevoice import load_vibevoicetts

TTS_PROCESS = None
CURRENT_ENGINE = None

CONFIG_FILE = "tts_service.json"
DEFAULT_PORT = 5001


# =========================
# PORT UTILS
# =========================

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def find_free_port(start=5001, max_tries=50):
    for i in range(max_tries):
        port = start + i
        if is_port_free(port):
            return port
    raise RuntimeError("No free port found for TTS")


# =========================
# CONFIG
# =========================

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("[TTS] failed to save config:", e)


def get_port():
    cfg = load_config()
    port = cfg.get("port")

    if port and is_port_free(port):
        return port

    # если порт занят или нет — ищем новый
    port = find_free_port(DEFAULT_PORT)
    cfg["port"] = port
    save_config(cfg)

    return port


def get_url():
    port = get_port()
    return f"http://127.0.0.1:{port}"


# =========================
# SERVICE CONTROL
# =========================

def is_service_running(url=None):
    import requests

    url = url or get_url()

    try:
        requests.get(url, timeout=0.5)
        return True
    except:
        return False


def stop_service():
    global TTS_PROCESS, CURRENT_ENGINE

    if TTS_PROCESS:
        print(f"[TTS] stopping {CURRENT_ENGINE}...")

        TTS_PROCESS.terminate()
        try:
            TTS_PROCESS.wait(timeout=3)
        except:
            TTS_PROCESS.kill()

        TTS_PROCESS = None
        CURRENT_ENGINE = None
        time.sleep(0.5)


# =========================
# START SERVICE
# =========================

def start_service(service_name):
    global TTS_PROCESS

    from os.path import join, dirname, abspath

    BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
    service_dir = join(BASE_DIR, "services", service_name)
    python_path = join(service_dir, "venv", "Scripts", "python.exe")

    port = get_port()
    url = f"http://127.0.0.1:{port}"

    print(f"[TTS] starting {service_name} on port {port}...")

    process = subprocess.Popen(
        [
            python_path,
            "-m",
            "uvicorn",
            "app:app",
            "--host", "127.0.0.1",
            "--port", str(port)
        ],
        cwd=service_dir
    )

    # ждём запуска
    for _ in range(40):
        if is_service_running(url):
            print(f"[TTS] {service_name} ready at {url}")
            TTS_PROCESS = process
            return
        time.sleep(0.25)

    process.kill()
    raise RuntimeError(f"{service_name} failed to start")


# =========================
# ENGINE SWITCH
# =========================

def load_engine():
    global CURRENT_ENGINE

    engine = get_tts_config().tts_engine

    if CURRENT_ENGINE == engine:
        return

    stop_service()

    if engine in ["omnivoice"]:
        start_service(engine)
        CURRENT_ENGINE = engine

    elif engine == "vibevoice":
        load_vibevoicetts()
        CURRENT_ENGINE = engine

    else:
        raise RuntimeError(f"Unknown TTS engine: {engine}")