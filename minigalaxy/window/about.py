import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from minigalaxy.version import VERSION
from minigalaxy.directories import LOGO_PATH, UI_DIR


@Gtk.Template.from_file(os.path.join(UI_DIR, "about.ui"))
class About(Gtk.AboutDialog):
    __gtype_name__ = "About"

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title="About", parent=parent, modal=True)
        self.set_version(VERSION)
        new_image = GdkPixbuf.Pixbuf().new_from_file(LOGO_PATH)
        self.set_logo(new_image)
