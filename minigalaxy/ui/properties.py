import gi
import os
import subprocess
import webbrowser

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib
from minigalaxy.paths import UI_DIR, THUMBNAIL_DIR
from minigalaxy.translation import _
from minigalaxy.launcher import config_game

@Gtk.Template.from_file(os.path.join(UI_DIR, "properties.ui"))
class Properties(Gtk.Dialog):
    __gtype_name__ = "Properties"
    gogBaseUrl = "https://www.gog.com"

    image = Gtk.Template.Child()
    button_properties_cancel = Gtk.Template.Child()
    button_properties_ok = Gtk.Template.Child()
    button_properties_support = Gtk.Template.Child()
    button_properties_store = Gtk.Template.Child()
    button_properties_open_files = Gtk.Template.Child()
    button_properties_settings = Gtk.Template.Child()
    switch_properties_show_fps = Gtk.Template.Child()
    entry_properties_variable = Gtk.Template.Child()
    entry_properties_command = Gtk.Template.Child()

    def __init__(self, parent, game, api):
        Gtk.Dialog.__init__(self, title=_("Properties"))
        self.parent = parent
        self.game = game
        self.api = api

        #Show the image
        self.load_thumbnail()

        # Disable/Enable buttons
        self.button_sensitive(game)

        # Retrieve variable & command each time Properties is open
        self.entry_properties_variable.set_text(self.game.get_info("variable"))
        self.entry_properties_command.set_text(self.game.get_info("command"))

    @Gtk.Template.Callback("on_button_properties_cancel_clicked")
    def cancel_pressed(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_ok_clicked")
    def ok_pressed(self, button):
        self.game.set_info("variable", str(self.entry_properties_variable.get_text()))
        self.game.set_info("command", str(self.entry_properties_command.get_text()))
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_settings_clicked")
    def on_menu_button_settings(self, widget):
        config_game(self.game)

    @Gtk.Template.Callback("on_button_properties_open_files_clicked")
    def on_menu_button_open_files(self, widget):
        self.game.set_install_dir()
        subprocess.call(["xdg-open", self.game.install_dir])

    @Gtk.Template.Callback("on_button_properties_support_clicked")
    def on_menu_button_support(self, widget):
        try:
            webbrowser.open(self.api.get_info(self.game)['links']['support'], new=2)
        except:
            self.parent.parent.show_error(
                _("Couldn't open support page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_button_properties_store_clicked")
    def on_menu_button_store(self, widget):
        webbrowser.open(self.gogBaseUrl + self.game.url)

    def load_thumbnail(self):
        thumbnail_cache_dir = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
        GLib.idle_add(self.image.set_from_file, thumbnail_cache_dir)

    def button_sensitive(self, game):
        if not game.is_installed():
            self.button_properties_open_files.set_sensitive(False)
            self.button_properties_settings.set_sensitive(False)
            self.entry_properties_command.set_sensitive(False)
            self.entry_properties_variable.set_sensitive(False)
            self.button_properties_support.set_sensitive(False)
            self.switch_properties_show_fps.set_sensitive(False)
        else:
            if game.platform == 'linux':
                self.button_properties_settings.set_sensitive(False)