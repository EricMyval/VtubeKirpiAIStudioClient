API_URL = "https://kirpi-gpt.ru/api/client/poll"
API_BASE = "https://kirpi-gpt.ru"
WIDGETS_URL = "https://kirpi-gpt.ru/api/client/widgets"
LAST_EVENT_URL = f"{API_URL.rsplit('/',1)[0]}/last-event-id"
POLL_INTERVAL = 1.0

PLATFORM_TYPE_TWITCH_POINTS = "twitch_points"
PLATFORM_TYPE_TWITCH_RAID = "twitch_raid"
PLATFORM_TYPE_TWITCH_FOLLOW = "twitch_follow"
PLATFORM_TYPE_TWITCH_CHAT = "twitch_chat"
PLATFORM_TYPE_TWITCH_VOICE = "twitch_voice"
PLATFORM_TYPE_TWITCH_AI = "twitch_ai"

PLATFORM_TYPE_DONATION_ALERTS = "donationalerts"
PLATFORM_TYPE_DONATION_ALERTS_AI = "donationalerts_ai"

PLATFORM_TYPE_DONATTY = "donatty"
PLATFORM_TYPE_DONATTY_AI = "donatty_ai"

PLATFORM_TYPE_AFK_START = "afk_start"
PLATFORM_TYPE_AFK_STOP = "afk_stop"

PLATFORM_TYPE_DONATE_PANEL = "donate_panel"