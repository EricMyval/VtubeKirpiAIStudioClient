# main.py
import sys
import threading
from modules.client.runtime.client_queue import clientEventQueue
from modules.client.runtime.client_worker import clientWorker
from modules.client.runtime.poller import ClientPoller
from modules.client.tts.config import bootstrap_tts
from modules.client.tts.service import load_tts
from modules.web_admin.web_admin import start_web_admin

if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    start_web_admin()
    bootstrap_tts()
    load_tts()

    clientPoller = ClientPoller(clientEventQueue, clientWorker)
    threading.Thread(target=clientPoller.start, daemon=True).start()

    print("🚀 Kirpi AI Client started")

    threading.Event().wait()