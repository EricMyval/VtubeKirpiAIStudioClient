CLIENT_POLL = "https://kirpi-gpt.ru/api/client/poll"
LAST_EVENT_URL = "https://kirpi-gpt.ru/api/client/last-event-id"
DONATE_PANEL_ACTIVE_SET = "https://kirpi-gpt.ru/widgets/donate-panel/active"
DONATE_PANEL_ACTIVE_CLEAR = "https://kirpi-gpt.ru/widgets/donate-panel/active/clear"
POLL_INTERVAL = 1.0
PAUSED_INTERVAL = 0.5
PLATFORM_TYPE_TWITCH_POINTS = "twitch_points"

def transliterate_lower(text: str) -> str:
    text = text.lower()
    rules = [
        ("shch", "щ"),
        ("sch", "щ"),
        ("ya", "я"),
        ("yo", "ё"),
        ("yu", "ю"),
        ("ye", "е"),
        ("yi", "и"),
        ("ee", "и"),
        ("zh", "ж"),
        ("ch", "ч"),
        ("sh", "ш"),
        ("th", "т"),
        ("kh", "х"),
        ("ph", "ф"),
        ("ts", "ц"),
        ("a", "а"), ("b", "б"), ("v", "в"), ("g", "г"), ("d", "д"),
        ("e", "е"), ("z", "з"), ("i", "и"), ("j", "ж"), ("k", "к"),
        ("l", "л"), ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"),
        ("r", "р"), ("s", "с"), ("t", "т"), ("u", "у"), ("f", "ф"),
        ("h", "х"), ("c", "к"), ("q", "к"), ("w", "в"), ("x", "кс"),
        ("y", "й"),
    ]
    for latin, cyr in rules:
        text = text.replace(latin, cyr)
    return text

def transliterate_cyr_to_lat(text: str) -> str:
    lat = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
        "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
        "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
        "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
        "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
        "ш": "sh", "щ": "sch", "ы": "y", "э": "e",
        "ю": "yu", "я": "ya",
    }
    text = text.lower()
    result = []
    for ch in text:
        if ch in lat:
            result.append(lat[ch])
        else:
            result.append(ch)
    return "".join(result)