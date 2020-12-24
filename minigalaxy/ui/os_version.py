import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.config import Config

@Gtk.Template.from_file(os.path.join(UI_DIR, "os_version.ui"))
class OS_Version(Gtk.Dialog):
    __gtype_name__ = "OS_Version"

    button_os_version_linux = Gtk.Template.Child()
    button_os_version_windows = Gtk.Template.Child()

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title=_("OS Version available"), modal=True)
        self.parent = parent

    @Gtk.Template.Callback("on_button_os_version_linux_clicked")
    def os_version_linux(self, widget):
        Config.set("OS_Version", "linux")
        self.destroy()

    @Gtk.Template.Callback("on_button_os_version_windows_clicked")
    def os_version_windows(self, widget):
        Config.set("OS_Version", "windows")
        self.destroy()