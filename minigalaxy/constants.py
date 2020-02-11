from minigalaxy.translation import _
from minigalaxy.version import VERSION
from minigalaxy.paths import DEFAULT_INSTALL_DIR

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
]

# The default values for new configuration files
DEFAULT_CONFIGURATION = {
    "config_version": VERSION,
    "lang": "en",
    "install_dir": DEFAULT_INSTALL_DIR,
    "keep_installers": False,
    "stay_logged_in": True,
    "show_fps": False
}

# Game IDs to ignore when received by the API
IGNORE_GAME_IDS = [
    1424856371,  # Hotline Miami 2: Wrong Number - Digital Comics
]

DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB
