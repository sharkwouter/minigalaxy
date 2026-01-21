from minigalaxy.version import VERSION
from minigalaxy.translation import _
from minigalaxy.ui.gtk import Gtk, load_ui, load_pixbuf


@Gtk.Template(string=load_ui("about.ui"))
class About(Gtk.AboutDialog):
    __gtype_name__ = "About"

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self, title=_("About"), parent=parent, modal=True)
        self.set_version(VERSION)
        new_image = load_pixbuf("io.github.sharkwouter.Minigalaxy.png")
        self.set_logo(new_image)
