# main.py

import sys
import threading

from modules.client.runtime.config_loader import ClientConfigLoader
from modules.client.tts.config import init_tts_config
from modules.client.tts.service import load_tts
from modules.web_admin.web_admin import start_web_admin
from modules.client.runtime.client_queue import ClientEventQueue
from modules.client.runtime.client_worker import ClientWorker
from modules.client.runtime.poller import ClientPoller


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    start_web_admin()

    print("[Client] loading configs...")
    tts_data = ClientConfigLoader.load_tts_config()
    init_tts_config(tts_data)

    print("[Client] loading TTS model...")
    load_tts()

    print("[Client] loading Client Event Queue...")
    queue = ClientEventQueue()
    worker = ClientWorker(queue)
    worker.start()

    print("[Client] loading Client Poller...")
    poller = ClientPoller(queue, worker)

    threading.Thread(
        target=poller.start,
        daemon=True
    ).start()

    print("🚀 Kirpi AI Client started")

    threading.Event().wait()