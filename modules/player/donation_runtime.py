# modules/player/donation_runtime.py
from threading import Event, Lock

# ==========================================================
# Runtime state (НЕ ЗАВИСИТ НИ ОТ ЧЕГО)
# ==========================================================

donations_enabled = Event()
donations_enabled.set()

stats_lock = Lock()
active_lock = Lock()

total_enqueued = 0
active_donations: set[float] = set()


# ==========================================================
# Public API
# ==========================================================

def pause_donations():
    donations_enabled.clear()


def resume_donations():
    donations_enabled.set()


def donations_are_enabled() -> bool:
    return donations_enabled.is_set()


def inc_stats():
    global total_enqueued
    with stats_lock:
        total_enqueued += 1


def register_donation(message_id: float):
    with active_lock:
        active_donations.add(message_id)


def finish_donation(message_id: float):
    with active_lock:
        active_donations.discard(message_id)


def get_queue_stats(donation_monitor=None):
    with stats_lock, active_lock:
        db_count = (
            donation_monitor.db.count_donations()
            if donation_monitor and donation_monitor.db
            else 0
        )

        return {
            "donations_enabled": donations_enabled.is_set(),
            "total_enqueued": total_enqueued,
            "donations_in_queue": len(active_donations),
            "current_queue_size": db_count + len(active_donations),
        }