import sys
import threading
from modules.runtime.client_worker import clientWorker
from modules.runtime.poller import ClientPoller
from modules.tts.engine import load_model
from modules.tts.generator import ttsGenerator  # НЕ УБИРАТЬ
from modules.web_admin.web_admin import start_web_admin

def run():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    start_web_admin()
    clientPoller = ClientPoller(clientWorker)
    threading.Thread(
        target=clientPoller.start,
        daemon=True
    ).start()
    load_model()
    print("🚀 Kirpi AI Client started")
    threading.Event().wait()

if __name__ == "__main__":
    run()