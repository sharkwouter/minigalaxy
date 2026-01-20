import os
import shutil
import subprocess

from minigalaxy.config import Config
from minigalaxy.installer import create_applications_file
from minigalaxy.paths import UI_DIR
from minigalaxy.translation import _
from minigalaxy.launcher import config_game, regedit_game, winetricks_game
from minigalaxy.ui.gtk import Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "properties.ui"))
class Properties(Gtk.Dialog):
    __gtype_name__ = "Properties"
    gogBaseUrl = "https://www.gog.com"

    button_properties_regedit = Gtk.Template.Child()
    button_properties_winecfg = Gtk.Template.Child()
    button_properties_winetricks = Gtk.Template.Child()
    button_properties_open_files = Gtk.Template.Child()
    switch_properties_check_for_updates = Gtk.Template.Child()
    button_properties_reset_os = Gtk.Template.Child()
    button_properties_reset_isa = Gtk.Template.Child()
    switch_properties_show_fps = Gtk.Template.Child()
    switch_properties_hide_game = Gtk.Template.Child()
    switch_properties_use_gamemode = Gtk.Template.Child()
    switch_properties_use_mangohud = Gtk.Template.Child()
    entry_properties_variable = Gtk.Template.Child()
    entry_properties_command = Gtk.Template.Child()
    button_properties_cancel = Gtk.Template.Child()
    button_properties_ok = Gtk.Template.Child()
    button_properties_os_translator = Gtk.Template.Child()
    button_properties_isa_translator = Gtk.Template.Child()

    def __init__(self, parent_library, game, config: Config, api):
        Gtk.Dialog.__init__(self, title=_("Properties of {}").format(game.name), parent=parent_library.parent_window,
                            modal=True)
        self.parent_library = parent_library
        self.parent_window = parent_library.parent_window
        self.game = game
        self.config = config
        self.api = api
        self.gamesdb_info = self.api.get_gamesdb_info(self.game)

        # Disable/Enable buttons
        self.button_sensitive(game)

        # Keep switch check for updates disabled/enabled
        self.switch_properties_check_for_updates.set_active(self.game.get_info("check_for_updates"))

        # Keep switch FPS disabled/enabled
        self.switch_properties_show_fps.set_active(self.game.get_info("show_fps"))

        # Keep switch game shown/hidden
        self.switch_properties_hide_game.set_active(self.game.get_info("hide_game"))

        # Keep switch use GameMode disabled/enabled
        self.switch_properties_use_gamemode.set_active(self.game.get_info("use_gamemode"))

        # Keep switch use MangoHud disabled/enabled
        self.switch_properties_use_mangohud.set_active(self.game.get_info("use_mangohud"))

        # Retrieve variable & command each time properties is open
        self.entry_properties_variable.set_text(self.game.get_info("variable"))
        self.entry_properties_command.set_text(self.game.get_info("command"))

        # Set OS translator (Wine, Proton, etc.)
        # First check for custom_wine (legacy), then os_translator_exec, then default to system wine
        os_exec = self.game.get_info("os_translator_exec") or self.game.get_info("custom_wine")
        if os_exec:
            self.button_properties_os_translator.set_filename(os_exec)
        elif shutil.which("wine"):
            self.button_properties_os_translator.set_filename(shutil.which("wine"))

        # Set ISA translator (FEX, QEMU, etc.)
        isa_exec = self.game.get_info("isa_translator_exec")
        if isa_exec:
            self.button_properties_isa_translator.set_filename(isa_exec)

    @Gtk.Template.Callback("on_button_properties_cancel_clicked")
    def cancel_pressed(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_ok_clicked")
    def ok_pressed(self, button):
        game_installed = self.game.is_installed()
        if game_installed:
            self.game.set_info("check_for_updates", self.switch_properties_check_for_updates.get_active())
            # Save OS/ISA translator executable paths
            os_exec = self.button_properties_os_translator.get_filename()
            isa_exec = self.button_properties_isa_translator.get_filename()
            if os_exec:
                self.game.set_info("os_translator_exec", os_exec)
            if isa_exec:
                self.game.set_info("isa_translator_exec", isa_exec)
            if self.switch_properties_use_gamemode.get_active() and not shutil.which("gamemoderun"):
                self.parent_window.show_error(_("GameMode wasn't found. Using GameMode cannot be enabled."))
                self.game.set_info("use_gamemode", False)
            else:
                self.game.set_info("use_gamemode", self.switch_properties_use_gamemode.get_active())
            if self.switch_properties_use_mangohud.get_active() and not shutil.which("mangohud"):
                self.parent_window.show_error(_("MangoHud wasn't found. Using MangoHud cannot be enabled."))
                self.game.set_info("use_mangohud", False)
            else:
                self.game.set_info("use_mangohud", self.switch_properties_use_mangohud.get_active())
        self.game.set_info("variable", str(self.entry_properties_variable.get_text()))
        self.game.set_info("command", str(self.entry_properties_command.get_text()))
        self.game.set_info("hide_game", self.switch_properties_hide_game.get_active())

        # Save OS translator to both fields for backward compatibility
        os_exec = self.button_properties_os_translator.get_filename()
        if os_exec:
            self.game.set_info("os_translator_exec", os_exec)
            self.game.set_info("custom_wine", os_exec)  # Keep for backward compatibility

        self.parent_library.filter_library()

        if game_installed and self.config.create_applications_file:
            create_applications_file(game=self.game, override=True)

        self.destroy()

    @Gtk.Template.Callback("on_button_properties_regedit_clicked")
    def on_menu_button_regedit(self, widget):
        regedit_game(self.game)

    @Gtk.Template.Callback("on_button_properties_reset_os_clicked")
    def on_menu_button_reset_os(self, widget):
        wine_path = shutil.which("wine")
        if wine_path:
            self.button_properties_os_translator.select_filename(wine_path)
            self.game.set_info("os_translator_exec", None)
            self.game.set_info("custom_wine", None)

    @Gtk.Template.Callback("on_button_properties_reset_isa_clicked")
    def on_menu_button_reset_isa(self, widget):
        self.button_properties_isa_translator.unselect_all()
        self.game.set_info("isa_translator_exec", None)

    @Gtk.Template.Callback("on_button_properties_winecfg_clicked")
    def on_menu_button_winecfg(self, widget):
        config_game(self.game)

    @Gtk.Template.Callback("on_button_properties_winetricks_clicked")
    def on_menu_button_winetricks(self, widget):
        # Check if using Proton, prefer protontricks
        os_exec = self.button_properties_os_translator.get_filename()

        if os_exec and "proton" in os_exec.lower():
            # Using Proton
            if not shutil.which("protontricks") and not shutil.which("winetricks"):
                self.parent_window.show_error(_("Neither Protontricks nor Winetricks were found."))
                return
        else:
            # Using Wine or other
            if not shutil.which("winetricks"):
                self.parent_window.show_error(_("Winetricks wasn't found and cannot be used."))
                return

        winetricks_game(self.game)

    @Gtk.Template.Callback("on_button_properties_open_files_clicked")
    def on_menu_button_open_files(self, widget):
        subprocess.call(["xdg-open", self.game.install_dir])

    def button_sensitive(self, game):
        if not game.is_installed():
            self.button_properties_open_files.set_sensitive(False)
            self.button_properties_os_translator.set_sensitive(False)
            self.button_properties_isa_translator.set_sensitive(False)
            self.button_properties_reset_os.set_sensitive(False)
            self.button_properties_reset_isa.set_sensitive(False)
            self.button_properties_regedit.set_sensitive(False)
            self.button_properties_winecfg.set_sensitive(False)
            self.button_properties_winetricks.set_sensitive(False)
            self.switch_properties_check_for_updates.set_sensitive(False)
            self.switch_properties_show_fps.set_sensitive(False)
            self.switch_properties_use_gamemode.set_sensitive(False)
            self.switch_properties_use_mangohud.set_sensitive(False)
            self.entry_properties_variable.set_sensitive(False)
            self.entry_properties_command.set_sensitive(False)

        if game.platform == 'linux':
            self.button_properties_regedit.hide()
            self.button_properties_winecfg.hide()
            self.button_properties_winetricks.hide()
            self.button_properties_os_translator.hide()
            self.button_properties_reset_os.hide()
