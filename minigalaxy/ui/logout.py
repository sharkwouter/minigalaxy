import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
import shutil
from minigalaxy.config import Config
from minigalaxy.paths import UI_DIR
from minigalaxy.translation import _


@Gtk.Template.from_file(os.path.join(UI_DIR, "logout.ui"))
class Logout(Gtk.Dialog):
    __gtype_name__ = "Logout"

    button_cancel = Gtk.Template.Child()
    button_ok = Gtk.Template.Child()

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title=_("Logout"), parent=parent, modal=True)
        self.parent = parent

    @Gtk.Template.Callback("on_button_ok_clicked")
    def ok_pressed(self, button):
        self.destroy()

        # Unset everything which is specific to this user
        self.parent.HeaderBar.set_subtitle("")
        Config.unset("username")
        Config.unset("refresh_token")
        self.parent.hide()

        # Show the login screen
        self.parent.__authenticate()
        self.parent.HeaderBar.set_subtitle(self.api.get_user_info())
        self.parent.sync_library()

        self.parent.show_all()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
