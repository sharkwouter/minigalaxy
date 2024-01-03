import os

from minigalaxy.paths import UI_DIR, SPLASH_IMAGE_PATH
from minigalaxy.ui.gtk import Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "loadingscreen.ui"))
class LoadingScreen(Gtk.Dialog):
    __gtype_name__ = "LoadingScreen"

    splash_image = Gtk.Template.Child()
    splash_label = Gtk.Template.Child()

    def __init__(self):
        super().__init__(title="Loading - Minigalaxy", modal=True)
        self.splash_image.set_from_file(SPLASH_IMAGE_PATH)
        self.show_all()
