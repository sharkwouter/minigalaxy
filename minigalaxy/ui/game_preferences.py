import os
import subprocess

from minigalaxy.paths import UI_DIR
from minigalaxy.translation import _
from minigalaxy.launcher import config_game, regedit_game
from minigalaxy.ui.gtk import Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "game_preferences.ui"))
class GamePreferences(Gtk.Dialog):
    __gtype_name__ = "GamePreferences"
    gogBaseUrl = "https://www.gog.com"

    button_game_preferences_cancel = Gtk.Template.Child()
    button_game_preferences_ok = Gtk.Template.Child()
    button_game_preferences_open_files = Gtk.Template.Child()
    button_game_preferences_winecfg = Gtk.Template.Child()
    button_game_preferences_regedit = Gtk.Template.Child()
    switch_game_preferences_show_fps = Gtk.Template.Child()
    switch_game_preferences_hide_game = Gtk.Template.Child()
    entry_game_preferences_variable = Gtk.Template.Child()
    entry_game_preferences_command = Gtk.Template.Child()

    def __init__(self, parent, game, api):
        Gtk.Dialog.__init__(self, title=_("Properties of {}").format(game.name), parent=parent.parent.parent,
                            modal=True)
        self.parent = parent
        self.game = game
        self.api = api
        self.gamesdb_info = self.api.get_gamesdb_info(self.game)

        # Disable/Enable buttons
        self.button_sensitive(game)

        # Retrieve variable & command each time Game Preferences is open
        self.entry_game_preferences_variable.set_text(self.game.get_info("variable"))
        self.entry_game_preferences_command.set_text(self.game.get_info("command"))

        # Keep switch FPS disabled/enabled
        self.switch_game_preferences_show_fps.set_active(self.game.get_info("show_fps"))

        # Keep switch game shown/hidden
        self.switch_game_preferences_hide_game.set_active(self.game.get_info("hide_game"))

        # Center game preferences window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

    @Gtk.Template.Callback("on_button_game_preferences_cancel_clicked")
    def cancel_pressed(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_game_preferences_ok_clicked")
    def ok_pressed(self, button):
        if self.game.is_installed():
            self.game.set_info("variable", str(self.entry_game_preferences_variable.get_text()))
            self.game.set_info("command", str(self.entry_game_preferences_command.get_text()))
            self.game.set_info("show_fps", self.switch_game_preferences_show_fps.get_active())
        self.game.set_info("hide_game", self.switch_game_preferences_hide_game.get_active())
        self.parent.parent.filter_library()
        self.destroy()

    @Gtk.Template.Callback("on_button_game_preferences_winecfg_clicked")
    def on_menu_button_winecfg(self, widget):
        config_game(self.game)

    @Gtk.Template.Callback("on_button_game_preferences_regedit_clicked")
    def on_menu_button_regedit(self, widget):
        regedit_game(self.game)

    @Gtk.Template.Callback("on_button_game_preferences_open_files_clicked")
    def on_menu_button_open_files(self, widget):
        self.game.set_install_dir()
        subprocess.call(["xdg-open", self.game.install_dir])

    def button_sensitive(self, game):
        if not game.is_installed():
            self.button_game_preferences_open_files.set_sensitive(False)
            self.button_game_preferences_winecfg.set_sensitive(False)
            self.entry_game_preferences_command.set_sensitive(False)
            self.entry_game_preferences_variable.set_sensitive(False)
            self.button_game_preferences_regedit.set_sensitive(False)
            self.switch_game_preferences_show_fps.set_sensitive(False)

        if game.platform == 'linux':
            self.button_game_preferences_winecfg.hide()
            self.button_game_preferences_regedit.hide()
