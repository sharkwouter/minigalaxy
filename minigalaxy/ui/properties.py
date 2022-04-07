import os
import shutil
import subprocess
import requests

from minigalaxy.paths import UI_DIR, CACHE_DIR
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
    switch_properties_show_fps = Gtk.Template.Child()
    switch_properties_hide_game = Gtk.Template.Child()
    switch_properties_use_gamemode = Gtk.Template.Child()
    switch_properties_use_mangohud = Gtk.Template.Child()
    switch_properties_use_dxvk = Gtk.Template.Child()
    entry_properties_variable = Gtk.Template.Child()
    entry_properties_command = Gtk.Template.Child()
    button_properties_cancel = Gtk.Template.Child()
    button_properties_ok = Gtk.Template.Child()
    dxvk_label = Gtk.Template.Child()

    def __init__(self, parent, game, api):
        Gtk.Dialog.__init__(self, title=_("Properties of {}").format(game.name), parent=parent.parent.parent,
                            modal=True)
        self.parent = parent
        self.game = game
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

        # Keep switch use DXVK disabled/enabled
        self.switch_properties_use_dxvk.set_active(self.game.get_info("use_dxvk"))

        # Retrieve variable & command each time properties is open
        self.entry_properties_variable.set_text(self.game.get_info("variable"))
        self.entry_properties_command.set_text(self.game.get_info("command"))

        # Center properties window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

    @Gtk.Template.Callback("on_button_properties_cancel_clicked")
    def cancel_pressed(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_ok_clicked")
    def ok_pressed(self, button):
        if self.game.is_installed():
            self.game.set_info("check_for_updates", self.switch_properties_check_for_updates.get_active())
            self.game.set_info("show_fps", self.switch_properties_show_fps.get_active())
            if self.switch_properties_use_gamemode.get_active() and not shutil.which("gamemoderun"):
                self.parent.parent.parent.show_error(_("GameMode wasn't found. Using GameMode cannot be enabled."))
                self.game.set_info("use_gamemode", False)
            else:
                self.game.set_info("use_gamemode", self.switch_properties_use_gamemode.get_active())
            if self.switch_properties_use_mangohud.get_active() and not shutil.which("mangohud"):
                self.parent.parent.parent.show_error(_("MangoHud wasn't found. Using MangoHud cannot be enabled."))
                self.game.set_info("use_mangohud", False)
            else:
                self.game.set_info("use_mangohud", self.switch_properties_use_mangohud.get_active())
            if not self.switch_properties_use_dxvk.get_active():
                self.install_uninstall_dxvk("uninstall", self.game)
                self.game.set_info("use_dxvk", False)
            else:
                self.game.set_info("use_dxvk", self.switch_properties_use_dxvk.get_active())
                self.install_uninstall_dxvk("install", self.game)

            self.game.set_info("variable", str(self.entry_properties_variable.get_text()))
            self.game.set_info("command", str(self.entry_properties_command.get_text()))
        self.game.set_info("hide_game", self.switch_properties_hide_game.get_active())
        self.parent.parent.filter_library()
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_regedit_clicked")
    def on_menu_button_regedit(self, widget):
        regedit_game(self.game)

    @Gtk.Template.Callback("on_button_properties_winecfg_clicked")
    def on_menu_button_winecfg(self, widget):
        config_game(self.game)

    @Gtk.Template.Callback("on_button_properties_winetricks_clicked")
    def on_menu_button_winetricks(self, widget):
        if not shutil.which("winetricks"):
            self.parent.parent.parent.show_error(_("Winetricks wasn't found and cannot be used."))
        else:
            winetricks_game(self.game)

    @Gtk.Template.Callback("on_button_properties_open_files_clicked")
    def on_menu_button_open_files(self, widget):
        self.game.set_install_dir()
        subprocess.call(["xdg-open", self.game.install_dir])

    # Check if a new version is available
    def check_for_dxvk(self):
        version = self.api.get_info_dxvk()
        dxvk_archive = os.path.join(CACHE_DIR, "dxvk-{}.tar.gz".format(version))

        if not os.path.isfile(dxvk_archive):
            url = "https://github.com/doitsujin/dxvk/releases/download/v{}/dxvk-{}.tar.gz".format(version, version)
            r = requests.get(url, allow_redirects=True)
            open('{}/dxvk-{}.tar.gz'.format(CACHE_DIR, version), 'wb').write(r.content)

        shutil.unpack_archive(dxvk_archive, CACHE_DIR)

    # Install DXVK
    def install_uninstall_dxvk(self, state, game):
        version = self.api.get_info_dxvk()
        dxvk_folder = os.path.join(CACHE_DIR, "dxvk-{}".format(version))
        if not dxvk_folder:
            self.check_for_dxvk()

        prefix = os.path.join(game.install_dir, "prefix")
        os.environ["WINEPREFIX"] = prefix

        setup_dxvk = os.path.join(dxvk_folder, "setup_dxvk.sh")

        if state == "install":
            subprocess.Popen([setup_dxvk, 'install'])
        if state == "uninstall":
            subprocess.Popen([setup_dxvk, 'uninstall'])

    def button_sensitive(self, game):
        if not game.is_installed():
            self.button_properties_regedit.set_sensitive(False)
            self.button_properties_winecfg.set_sensitive(False)
            self.button_properties_winetricks.set_sensitive(False)
            self.button_properties_open_files.set_sensitive(False)
            self.switch_properties_check_for_updates.set_sensitive(False)
            self.switch_properties_show_fps.set_sensitive(False)
            self.switch_properties_use_gamemode.set_sensitive(False)
            self.switch_properties_use_mangohud.set_sensitive(False)
            self.switch_properties_use_dxvk.set_sensitive(False)
            self.entry_properties_variable.set_sensitive(False)
            self.entry_properties_command.set_sensitive(False)

        if game.platform == 'linux':
            self.button_properties_regedit.hide()
            self.button_properties_winecfg.hide()
            self.button_properties_winetricks.hide()
            self.switch_properties_use_dxvk.hide()
            self.dxvk_label.hide()
