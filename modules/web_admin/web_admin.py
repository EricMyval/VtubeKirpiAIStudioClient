import threading
import webbrowser
import time
from flask import render_template

from modules.web_admin import app
from modules.web_admin.config import get_host, get_port, get_base_url


@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# BASE_URL для всех HTML
# ==========================================

@app.context_processor
def inject_base_url():
    return {
        "BASE_URL": get_base_url()
    }


# ==========================================
# SERVER START
# ==========================================

def start_web_admin():

    host = get_host()
    port = get_port()

    def _run():

        print(f"🌐 Web Admin running: http://{host}:{port}/")

        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False
        )

    th = threading.Thread(target=_run, daemon=True)
    th.start()

    # даём серверу время стартовать
    time.sleep(1)

    # открываем браузер
    try:
        webbrowser.open(f"http://{host}:{port}/")
    except Exception as e:
        print("Не удалось открыть браузер:", e)

    return th