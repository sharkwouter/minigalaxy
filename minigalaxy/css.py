from minigalaxy.data import get_data_file
from minigalaxy.logger import logger
from minigalaxy.ui.gtk import Gtk, Gdk


CSS_PROVIDER = Gtk.CssProvider()


def load_css():
    """
    Load CSS data.
    """
    try:
        css_data = get_data_file("style.css").read_text(encoding='utf-8')
        CSS_PROVIDER.load_from_data(css_data)
    except Exception:
        logger.error("The CSS could not be loaded", exc_info=1)
    Gtk.StyleContext().add_provider_for_screen(Gdk.Screen.get_default(), CSS_PROVIDER, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
