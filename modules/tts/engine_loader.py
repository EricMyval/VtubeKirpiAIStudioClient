import subprocess
import time
from modules.tts.config import get_tts_config
from modules.tts.voice_vibevoice import load_vibevoicetts

TTS_PROCESS = None
CURRENT_ENGINE = None

def load_engine():
    global CURRENT_ENGINE
    engine = get_tts_config().tts_engine
    if CURRENT_ENGINE == engine:
        return
    stop_service()
    if engine in ["f5", "qwen3", "voxcpm2", "omnivoice"]:
        start_service(engine)
        CURRENT_ENGINE = engine
    elif engine == "vibevoice":
        load_vibevoicetts()
        CURRENT_ENGINE = engine
    else:
        raise RuntimeError(f"Unknown TTS engine: {engine}")

def is_service_running(url="http://127.0.0.1:5001"):
    import requests
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


def start_service(service_name):
    global TTS_PROCESS
    from os.path import join, dirname, abspath
    BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
    service_dir = join(BASE_DIR, "services", service_name)
    python_path = join(service_dir, "venv", "Scripts", "python.exe")
    print(f"[TTS] starting {service_name}...")
    process = subprocess.Popen(
        [
            python_path,
            "-m",
            "uvicorn",
            "app:app",
            "--host", "127.0.0.1",
            "--port", "5001"
        ],
        cwd=service_dir
    )
    for _ in range(30):
        if is_service_running():
            print(f"[TTS] {service_name} ready")
            TTS_PROCESS = process
            return
        time.sleep(0.3)
    process.kill()
    raise RuntimeError(f"{service_name} failed to start")