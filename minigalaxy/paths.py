import os
import sys

LAUNCH_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

CONFIG_DIR = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), "minigalaxy")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), "minigalaxy")

THUMBNAIL_DIR = os.path.join(CACHE_DIR, "thumbnails")
DEFAULT_INSTALL_DIR = os.path.expanduser("~/GOG Games")

UI_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/ui"))
if not os.path.exists(UI_DIR):
    UI_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/ui"))

LOGO_IMAGE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/icons/192x192/com.github.sharkwouter.minigalaxy.png"))
if not os.path.exists(LOGO_IMAGE_PATH):
    LOGO_IMAGE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/icons/hicolor/192x192/apps/com.github.sharkwouter.minigalaxy.png"))

ICON_WINE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/icons/20x20/winehq_logo_glass.png"))

LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/mo"))
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/translations"))
