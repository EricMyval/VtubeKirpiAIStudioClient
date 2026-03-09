from flask import Flask
from modules.utils.runtime_paths import app_root
import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

BASE_PATH = app_root()

app = Flask(
    __name__,
    template_folder=str(BASE_PATH / "templates"),
    static_folder=str(BASE_PATH / "static")
)

app.secret_key = "super-long-random-string-change-this-once-and-keep"


# импортируем основные роуты
from modules.web_admin import routes


# импортируем и регистрируем alerts widget
from modules.alerts.routes import bp as alerts_bp
app.register_blueprint(alerts_bp)