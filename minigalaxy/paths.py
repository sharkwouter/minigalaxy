import os

CONFIG_DIR = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), "minigalaxy")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), "minigalaxy")

THUMBNAIL_DIR = os.path.join(CACHE_DIR, "thumbnails")
DEFAULT_INSTALL_DIR = os.path.expanduser("~/GOG Games")

UI_DIR = "data/ui"
if not os.path.exists(UI_DIR):
    UI_DIR = "/usr/share/minigalaxy/ui"

LOGO_IMAGE_PATH = "data/minigalaxy.png"
if not os.path.exists(LOGO_IMAGE_PATH):
    LOGO_IMAGE_PATH = "/usr/share/icons/hicolor/192x192/apps/minigalaxy.png"

LOCALE_DIR = "data/mo"
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = "/usr/share/minigalaxy/translations"
