# BASE_URL = "https://kirpi-gpt.ru"
BASE_URL = "http://127.0.0.1:5000"

CLIENT_POLL = f"{BASE_URL}/api/client/poll"
LAST_EVENT_URL = f"{BASE_URL}/api/client/last-event-id"
DONATE_PANEL_ACTIVE_SET = f"{BASE_URL}/widgets/donate-panel/active"
DONATE_PANEL_ACTIVE_CLEAR = f"{BASE_URL}/widgets/donate-panel/active/clear"

POLL_INTERVAL = 1.0
PAUSED_INTERVAL = 0.5
PLATFORM_TYPE_TWITCH_POINTS = "twitch_points"