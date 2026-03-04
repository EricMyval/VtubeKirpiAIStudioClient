from flask import Blueprint, jsonify, render_template
from modules.player.donation_runtime import (
    pause_donations,
    resume_donations,
    get_queue_stats,
)
from modules.donation.donation_monitor import donation_monitor

donations_queue = Blueprint(
    "donations_queue",
    __name__,
    url_prefix="/donations-queue",
)

@donations_queue.route("/")
def page():
    return render_template("donations_queue.html")

@donations_queue.route("/status")
def status():
    return jsonify(get_queue_stats(donation_monitor))

@donations_queue.route("/pause", methods=["POST"])
def pause():
    pause_donations()
    return jsonify(success=True)

@donations_queue.route("/resume", methods=["POST"])
def resume():
    resume_donations()
    return jsonify(success=True)