import os

CONFIG_DIR = os.path.join(os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), "minigalaxy")
CACHE_DIR = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), "minigalaxy")

THUMBNAIL_DIR = os.path.join(CACHE_DIR, "thumbnails")
DEFAULT_INSTALL_DIR = os.path.expanduser("~/GOG Games")
