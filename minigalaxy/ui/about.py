import os
from minigalaxy.version import VERSION
from minigalaxy.translation import _
from minigalaxy.paths import LOGO_IMAGE_PATH, UI_DIR
from minigalaxy.ui.gtk import Gtk, GdkPixbuf


@Gtk.Template.from_file(os.path.join(UI_DIR, "about.ui"))
class About(Gtk.AboutDialog):
    __gtype_name__ = "About"

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self, title=_("About"), parent=parent, modal=True)
        self.set_version(VERSION)
        new_image = GdkPixbuf.Pixbuf().new_from_file(LOGO_IMAGE_PATH)
        self.set_logo(new_image)
