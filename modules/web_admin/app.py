from flask import Flask, request, redirect
from modules.utils.runtime_paths import app_root


def create_app():
    base = app_root()

    app = Flask(
        __name__,
        template_folder=str(base / "templates"),
        static_folder=str(base / "static"),
    )

    app.secret_key = "super-long-random-string-change-this-once-and-keep"

    @app.before_request
    def force_localhost():
        if request.host.startswith("127.0.0.1:"):
            return redirect(request.url.replace("127.0.0.1", "localhost"), 302)

    return app
