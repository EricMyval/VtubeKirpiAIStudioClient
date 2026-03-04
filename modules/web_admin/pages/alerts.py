from flask import Blueprint, render_template

bp_alerts = Blueprint(
    "alerts_pages",
    __name__,
    template_folder="../../../templates"
)


@bp_alerts.route("/alerts/settings")
def alerts_settings_page():
    return render_template("alerts/settings.html")


@bp_alerts.route("/alerts/widget")
def alerts_widget_page():
    return render_template("alerts/../../client/alerts/alerts_widget.html")
