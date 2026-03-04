# modules/web_admin/shared.py
from modules.twitch.twitch_alerts_settings import TwitchAlertsVoiceSettingsStore
from modules.twitch.twitch_follow_once_store import TwitchFollowOnceStore
from modules.chat.chat_to_donation_settings import ChatToDonationControllerSettings

chat_to_donation_settings = ChatToDonationControllerSettings()
twitch_follow_once = TwitchFollowOnceStore()
twitch_alerts_store = TwitchAlertsVoiceSettingsStore()



