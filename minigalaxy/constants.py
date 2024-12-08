from minigalaxy.translation import _

SUPPORTED_DOWNLOAD_LANGUAGES = [
    ["br", _("Brazilian Portuguese")],
    ["cn", _("Chinese")],
    ["da", _("Danish")],
    ["nl", _("Dutch")],
    ["en", _("English")],
    ["fi", _("Finnish")],
    ["fr", _("French")],
    ["de", _("German")],
    ["hu", _("Hungarian")],
    ["it", _("Italian")],
    ["jp", _("Japanese")],
    ["ko", _("Korean")],
    ["no", _("Norwegian")],
    ["pl", _("Polish")],
    ["pt", _("Portuguese")],
    ["ru", _("Russian")],
    ["es", _("Spanish")],
    ["sv", _("Swedish")],
    ["tr", _("Turkish")],
    ["ro", _("Romanian")],
]

SUPPORTED_LOCALES = [
    ["", _("System default")],
    ["pt_BR", _("Brazilian Portuguese")],
    ["cs_CZ", _("Czech")],
    ["nl", _("Dutch")],
    ["en_US", _("English")],
    ["fi", _("Finnish")],
    ["fr", _("French")],
    ["de", _("German")],
    ["it_IT", _("Italian")],
    ["nb_NO", _("Norwegian Bokmål")],
    ["nn_NO", _("Norwegian Nynorsk")],
    ["pl", _("Polish")],
    ["pt_PT", _("Portuguese")],
    ["ru_RU", _("Russian")],
    ["zh_CN", _("Simplified Chinese")],
    ["es", _("Spanish")],
    ["es_ES", _("Spanish (Spain)")],
    ["sv_SE", _("Swedish")],
    ["zh_TW", _("Traditional Chinese")],
    ["tr", _("Turkish")],
    ["uk", _("Ukrainian")],
    ["el", _("Greek")],
    ["ro", _("Romanian")],
]

VIEWS = [
    ["grid", _("Grid")],
    ["list", _("List")],
]

WINE_VARIANTS = [
    ["wine", _("Wine")],
    ["umu-run", _("UMU-Launcher")]
]

# Game IDs to ignore when received by the API
IGNORE_GAME_IDS = [
    1424856371,  # Hotline Miami 2: Wrong Number - Digital Comics
    1980301910,  # The Witcher Goodies Collection
    2005648906,  # Spring Sale Goodies Collection #1
    1486144755,  # Cyberpunk 2077 Goodies Collection
    1581684020,  # A Plague Tale Digital Goodies Pack
    1185685769,  # CDPR Goodie Pack Content
]

DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB

# This is the file size needed for the download manager to consider resuming worthwhile
MINIMUM_RESUME_SIZE = 50 * 1024**2  # 50 MB

# UI download threads are for UI assets like thumbnails or icons
UI_DOWNLOAD_THREADS = 4
# Game download threads are for long-running downloads like games, DLC or updates
GAME_DOWNLOAD_THREADS = 4
