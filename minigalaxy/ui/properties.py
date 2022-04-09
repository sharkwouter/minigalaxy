import os
import shutil
import subprocess
import requests
import hashlib

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
    switch_properties_use_dxvk_vkd3d = Gtk.Template.Child()
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
        self.switch_properties_use_dxvk_vkd3d.set_active(self.game.get_info("use_dxvk"))

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
            if self.switch_properties_use_dxvk_vkd3d.get_active():
                self.game.set_info("use_dxvk", self.switch_properties_use_dxvk_vkd3d.get_active())
                self.install_uninstall_dxvk_vkd3d("install", self.game)
            else:
                self.install_uninstall_dxvk_vkd3d("uninstall", self.game)
                self.game.set_info("use_dxvk", False)

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

    # Check if a new dxvk version is available
    def download_latest_dxvk(self, dxvk_dir):
        version = self.api.get_info_dxvk()
        dxvk_archive = os.path.join(dxvk_dir, "dxvk-{}.tar.gz".format(version))

        if not os.path.exists(dxvk_archive):
            url = "https://github.com/doitsujin/dxvk/releases/download/v{}/dxvk-{}.tar.gz".format(version, version)
            r = requests.get(url, allow_redirects=True)
            open('{}/dxvk-{}.tar.gz'.format(dxvk_dir, version), 'wb').write(r.content)

        shutil.unpack_archive(dxvk_archive, dxvk_dir)

        # Remove the archive and keep only DXVK folder
        os.remove(dxvk_archive)

    # Check if a new vkd3d-proton version is available
    def download_latest_vkd3d(self, vkd3d_dir):
        version = self.api.get_info_vkd3d()
        vkd3d_archive_zst = os.path.join(vkd3d_dir, "vkd3d-proton-{}.tar.zst".format(version))
        vkd3d_archive_tar = vkd3d_archive_zst[:-4]

        if not os.path.exists(vkd3d_archive_zst):
            url = "https://github.com/HansKristian-Work/vkd3d-proton/releases/download/v{}/vkd3d-proton-{}.tar.zst".format(
                version, version)
            r = requests.get(url, allow_redirects=True)
            open('{}/vkd3d-proton-{}.tar.zst'.format(vkd3d_dir, version), 'wb').write(r.content)

        # Use check_call to be sure that the command is finished before to continue.
        subprocess.check_call(['unzstd', vkd3d_archive_zst])
        shutil.unpack_archive(vkd3d_archive_tar, vkd3d_dir)

        # Remove both archive and keep only vkd3d-proton folder.
        os.remove(vkd3d_archive_zst)
        os.remove(vkd3d_archive_tar)

    # Install DXVK
    def install_uninstall_dxvk_vkd3d(self, state, game):
        DXVK_DIR = os.path.join(CACHE_DIR, 'DXVK')
        VKD3D_DIR = os.path.join(CACHE_DIR, 'VKD3D')

        dxvk_version = self.api.get_info_dxvk()
        dxvk_folder = os.path.join(DXVK_DIR, "dxvk-{}".format(dxvk_version))
        vkd3d_version = self.api.get_info_vkd3d()
        vkd3d_folder = os.path.join(VKD3D_DIR, "vkd3d-proton-{}".format(vkd3d_version))
        setup_dxvk = os.path.join(dxvk_folder, "setup_dxvk.sh")
        setup_vkd3d = os.path.join(vkd3d_folder, "setup_vkd3d_proton.sh")

        prefix = os.path.join(game.install_dir, "prefix")
        os.environ["WINEPREFIX"] = prefix

        if not os.path.exists(DXVK_DIR) and not os.path.exists(VKD3D_DIR):
            os.makedirs(DXVK_DIR, mode=0o755)
            os.makedirs(VKD3D_DIR, mode=0o755)

        if not os.path.exists(dxvk_folder) and not os.path.exists(vkd3d_folder):
            self.download_latest_vkd3d(VKD3D_DIR)
            self.download_latest_dxvk(DXVK_DIR)

        # Retrieve d3d9.dll hash
        d3d9_prefix = hashlib.md5(
            open((os.path.join(prefix, "dosdevices/c:/windows/system32/d3d9.dll")), 'rb').read()).hexdigest()
        d3d9_dxvk = hashlib.md5(open((os.path.join(dxvk_folder, "x64/d3d9.dll")), 'rb').read()).hexdigest()

        # DXVK/VKD3D are installed/uninstalled each time the user clicks on button_properties_ok.
        # Even if DXVK/VKD3D are already installed.
        # These conditions check if dxvk/vkd3d are installed in the prefix and avoid this issue.
        if d3d9_prefix != d3d9_dxvk and state == "install":
            subprocess.Popen([setup_dxvk, 'install'])
            subprocess.Popen([setup_vkd3d, 'install'])
        if d3d9_prefix == d3d9_dxvk and state == "uninstall":
            subprocess.Popen([setup_dxvk, 'uninstall'])
            subprocess.Popen([setup_vkd3d, 'uninstall'])

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
            self.switch_properties_use_dxvk_vkd3d.set_sensitive(False)
            self.entry_properties_variable.set_sensitive(False)
            self.entry_properties_command.set_sensitive(False)

        if game.platform == 'linux':
            self.button_properties_regedit.hide()
            self.button_properties_winecfg.hide()
            self.button_properties_winetricks.hide()
            self.switch_properties_use_dxvk_vkd3d.hide()
            self.dxvk_label.hide()
