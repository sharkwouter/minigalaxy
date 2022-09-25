import os
import sys

LAUNCH_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
if LAUNCH_DIR == "/bin" or LAUNCH_DIR == "/sbin":
    LAUNCH_DIR = "/usr" + LAUNCH_DIR

CONFIG_DIR = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), "minigalaxy")
CONFIG_GAMES_DIR = os.path.join(CONFIG_DIR, "games")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), "minigalaxy")

THUMBNAIL_DIR = os.path.join(CACHE_DIR, "thumbnails")
COVER_DIR = os.path.join(CACHE_DIR, "covers")
ICON_DIR = os.path.join(CACHE_DIR, "icons")
APPLICATIONS_DIR = os.path.expanduser("~/.local/share/applications")
DEFAULT_INSTALL_DIR = os.path.expanduser("~/GOG Games")

UI_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/ui"))
if not os.path.exists(UI_DIR):
    UI_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/ui"))

LOGO_IMAGE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/icons/192x192/io.github.sharkwouter.Minigalaxy.png"))
if not os.path.exists(LOGO_IMAGE_PATH):
    LOGO_IMAGE_PATH = os.path.abspath(
        os.path.join(LAUNCH_DIR, "../share/icons/hicolor/192x192/apps/io.github.sharkwouter.Minigalaxy.png")
    )

ICON_WINE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/images/winehq_logo_glass.png"))
if not os.path.exists(ICON_WINE_PATH):
    ICON_WINE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/images/winehq_logo_glass.png"))

LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/mo"))
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/translations"))

CSS_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/style.css"))
if not os.path.exists(CSS_PATH):
    CSS_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/style.css"))
