import os
import sys

LAUNCH_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
if LAUNCH_DIR == "/bin" or LAUNCH_DIR == "/sbin":
    LAUNCH_DIR = "/usr" + LAUNCH_DIR

CONFIG_DIR = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), "minigalaxy")
CONFIG_GAMES_DIR = os.path.join(CONFIG_DIR, "games")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), "minigalaxy")
DOWNLOAD_DIR = os.path.join(os.getenv('MINIGALAXY_DOWNLOAD_DIR', CACHE_DIR), "download")

THUMBNAIL_DIR = os.path.join(CACHE_DIR, "thumbnails")
COVER_DIR = os.path.join(CACHE_DIR, "covers")
ICON_DIR = os.path.join(CACHE_DIR, "icons")
CATEGORIES_FILE_PATH = os.path.join(CACHE_DIR, "categories.json")
APPLICATIONS_DIR = os.path.expanduser("~/.local/share/applications")
DEFAULT_INSTALL_DIR = os.path.expanduser("~/GOG Games")

LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/mo"))
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/translations"))
