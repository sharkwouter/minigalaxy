import requests
import platform
from minigalaxy.translation import _
from minigalaxy.version import VERSION

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
    ["ru_RU", _("Russian")],
    ["zh_CN", _("Simplified Chinese")],
    ["es", _("Spanish")],
    ["es_ES", _("Spanish (Spain)")],
    ["sv_SE", _("Swedish")],
    ["zh_TW", _("Traditional Chinese")],
    ["tr", _("Turkish")],
    ["uk", _("Ukrainian")],
]

VIEWS = [
    ["grid", _("Grid")],
    ["list", _("List")],
]

# Game IDs to ignore when received by the API
IGNORE_GAME_IDS = [
    1424856371,  # Hotline Miami 2: Wrong Number - Digital Comics
    1980301910,  # The Witcher Goodies Collection
    2005648906,  # Spring Sale Goodies Collection #1
    1486144755,  # Cyberpunk 2077 Goodies Collection
]

DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB

# This is the file size needed for the download manager to consider resuming worthwhile
MINIMUM_RESUME_SIZE = 50 * 1024**2  # 50 MB

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'Minigalaxy/{} (Linux {})'.format(VERSION, platform.machine())})
