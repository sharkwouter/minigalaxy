from minigalaxy.ui.gtk import Gtk
from minigalaxy.paths import CSS_PATH

CSS_PROVIDER = Gtk.CssProvider()
try:
    with open(CSS_PATH) as style:
        CSS_PROVIDER.load_from_data(style.read().encode('utf-8'))
except gi.repository.GLib.Error:
    print("The CSS in {} could not be loaded".format(CSS_PATH))
