import os
import sys

LAUNCH_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
if LAUNCH_DIR == "/bin" or LAUNCH_DIR == "/sbin":
    LAUNCH_DIR = "/usr" + LAUNCH_DIR

CONFIG_DIR = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), "minigalaxy")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), "minigalaxy")

THUMBNAIL_DIR = os.path.join(CACHE_DIR, "thumbnails")
DEFAULT_INSTALL_DIR = os.path.expanduser("~/GOG Games")

UI_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/ui"))
if not os.path.exists(UI_DIR):
    UI_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/ui"))

LOGO_IMAGE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/icons/192x192/io.github.sharkwouter.Minigalaxy.png"))
if not os.path.exists(LOGO_IMAGE_PATH):
    LOGO_IMAGE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/icons/hicolor/192x192/apps/io.github.sharkwouter.Minigalaxy.png"))

ICON_WINE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/images/winehq_logo_glass.png"))
if not os.path.exists(ICON_WINE_PATH):
    ICON_WINE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/images/winehq_logo_glass.png"))

ICON_UPDATE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/images/update_available.png"))
if not os.path.exists(ICON_UPDATE_PATH):
    ICON_UPDATE_PATH = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/images/update_available.png"))

ICON_CANCEL_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/images/process-stop.svg"))
if not os.path.exists(ICON_CANCEL_PATH_SVG):
    ICON_CANCEL_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/images/process-stop.svg"))

ICON_OK_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/images/dialog-apply.svg"))
if not os.path.exists(ICON_OK_PATH_SVG):
    ICON_OK_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/images/dialog-apply.svg"))

ICON_DOWNLOAD_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/images/go-bottom.svg"))
if not os.path.exists(ICON_DOWNLOAD_PATH_SVG):
    ICON_DOWNLOAD_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/images/go-bottom.svg"))

ICON_CDROM_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/images/media-optical.svg"))
if not os.path.exists(ICON_CDROM_PATH_SVG):
    ICON_CDROM_PATH_SVG = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/images/media-optical.svg"))

LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../data/mo"))
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = os.path.abspath(os.path.join(LAUNCH_DIR, "../share/minigalaxy/translations"))
