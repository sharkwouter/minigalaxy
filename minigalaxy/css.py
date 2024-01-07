from minigalaxy.logger import logger
from minigalaxy.ui.gtk import Gtk, Gdk
from minigalaxy.paths import CSS_PATH

CSS_PROVIDER = Gtk.CssProvider()


def load_css():
    try:
        with open(CSS_PATH) as style:
            CSS_PROVIDER.load_from_data(style.read().encode('utf-8'))
    except Exception:
        logger.error("The CSS in %s could not be loaded", CSS_PATH, exc_info=1)
    Gtk.StyleContext().add_provider_for_screen(Gdk.Screen.get_default(), CSS_PROVIDER, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
