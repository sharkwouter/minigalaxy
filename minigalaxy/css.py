from minigalaxy.ui.gtk import Gtk
from minigalaxy.paths import CSS_PATH

CSS_PROVIDER = Gtk.CssProvider()
with open(CSS_PATH) as style:
    CSS_PROVIDER.load_from_data(style.read().encode('utf-8'))
