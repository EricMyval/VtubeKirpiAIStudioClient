# main.py

import sys
import threading
from modules.runtime.client_worker import clientWorker
from modules.runtime.poller import ClientPoller
from modules.tts.config import bootstrap_tts
from modules.tts.engine_loader import load_engine
from modules.tts.generator import ttsGenerator # НЕ УБИРАТЬ
from modules.web_admin.web_admin import start_web_admin


if __name__ == "__main__":

    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    start_web_admin()

    bootstrap_tts()
    load_engine()

    clientPoller = ClientPoller(clientWorker)

    threading.Thread(
        target=clientPoller.start,
        daemon=True
    ).start()

    print("🚀 Kirpi AI Client started")

    threading.Event().wait()