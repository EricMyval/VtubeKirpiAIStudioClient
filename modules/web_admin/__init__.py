from flask import Flask
from modules.utils.runtime_paths import app_root
import logging

from modules.client.alerts.routes import bp as alerts_bp
from modules.client.roulette.overlay_routes import bp as roulette_overlay_bp
from modules.client.cabinet.routes import bp as client_cabinet_bp
from modules.client.audio.routes import bp as client_audio_bp
from modules.client.donate_panel.routes import bp as donate_panel_bp

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

BASE_PATH = app_root()
app = Flask( __name__, template_folder=str(BASE_PATH / "templates"), static_folder=str(BASE_PATH / "static"))
app.secret_key = "super-long-random-string-change-this-once-and-keep"

app.register_blueprint(roulette_overlay_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(client_cabinet_bp)
app.register_blueprint(client_audio_bp)
app.register_blueprint(donate_panel_bp)