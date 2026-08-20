import shutil
import subprocess

from minigalaxy.config import Config
from minigalaxy.compatibility import (
    CUSTOM_WINE_CHOICE_ID,
    PROTON_CHOICE_PREFIX,
    SYSTEM_WINE_CHOICE_ID,
    build_compatibility_choices,
    selected_compatibility_choice_id,
)
from minigalaxy.game import InfoKey
from minigalaxy.installer import create_applications_file
from minigalaxy.translation import _
from minigalaxy.launcher import config_game, regedit_game, winetricks_game
from minigalaxy.umu import (
    MINIMUM_UMU_VERSION_TEXT,
    UmuInstallError,
    get_umu_status,
    install_managed_umu,
)
from minigalaxy.ui.gtk import Gtk, load_ui


@Gtk.Template(string=load_ui("properties.ui"))
class Properties(Gtk.Dialog):
    __gtype_name__ = "Properties"
    gogBaseUrl = "https://www.gog.com"

    button_properties_regedit = Gtk.Template.Child()
    button_properties_winecfg = Gtk.Template.Child()
    button_properties_winetricks = Gtk.Template.Child()
    button_properties_open_files = Gtk.Template.Child()
    switch_properties_check_for_updates = Gtk.Template.Child()
    button_properties_wine = Gtk.Template.Child()
    button_properties_reset = Gtk.Template.Child()
    switch_properties_show_fps = Gtk.Template.Child()
    switch_properties_hide_game = Gtk.Template.Child()
    switch_properties_use_gamemode = Gtk.Template.Child()
    switch_properties_use_mangohud = Gtk.Template.Child()
    entry_properties_variable = Gtk.Template.Child()
    entry_properties_command = Gtk.Template.Child()
    button_properties_cancel = Gtk.Template.Child()
    button_properties_ok = Gtk.Template.Child()
    label_wine_custom = Gtk.Template.Child()
    label_properties_compatibility_tool = Gtk.Template.Child()
    combo_properties_compatibility = Gtk.Template.Child()
    label_properties_compatibility_path_title = Gtk.Template.Child()
    label_properties_compatibility_path = Gtk.Template.Child()
    button_properties_compatibility_refresh = Gtk.Template.Child()
    label_properties_umu_runtime_title = Gtk.Template.Child()
    label_properties_umu_runtime = Gtk.Template.Child()
    button_properties_umu_install = Gtk.Template.Child()

    def __init__(self, parent_library, game, config: Config, api):
        Gtk.Dialog.__init__(self, title=_("Properties of {}").format(game.name), parent=parent_library.parent_window,
                            modal=True)
        self.parent_library = parent_library
        self.parent_window = parent_library.parent_window
        self.game = game
        self.config = config
        self.api = api
        self._compatibility_choices = {}

        self.combo_properties_compatibility.connect(
            "changed",
            self._on_compatibility_changed,
        )
        self.button_properties_compatibility_refresh.connect(
            "clicked",
            self._on_compatibility_refresh,
        )
        self.button_properties_umu_install.connect(
            "clicked",
            self._on_umu_install,
        )
        self.button_properties_wine.connect(
            "file-set",
            self._on_custom_wine_file_set,
        )

        self.gamesdb_info = self.api.get_gamesdb_info(self.game)

        # Disable/Enable buttons
        self.button_sensitive(game)

        # Keep switch check for updates disabled/enabled
        self.switch_properties_check_for_updates.set_active(self.game.get_info(InfoKey.CHECK_UPDATES))

        # Retrieve custom wine path each time Properties is open
        if self.game.get_info(InfoKey.CUSTOM_WINE):
            self.button_properties_wine.set_filename(self.game.get_info(InfoKey.CUSTOM_WINE))
        elif shutil.which("wine"):
            self.button_properties_wine.set_filename(shutil.which("wine"))

        if self.game.platform == "windows":
            self._populate_compatibility_tools()

        # Keep switch FPS disabled/enabled
        self.switch_properties_show_fps.set_active(self.game.get_info(InfoKey.SHOW_FPS))

        # Keep switch game shown/hidden
        self.switch_properties_hide_game.set_active(self.game.get_info(InfoKey.HIDE_GAME))

        # Keep switch use GameMode disabled/enabled
        self.switch_properties_use_gamemode.set_active(self.game.get_info(InfoKey.GAMEMODE))

        # Keep switch use MangoHud disabled/enabled
        self.switch_properties_use_mangohud.set_active(self.game.get_info(InfoKey.MANGOHUD))

        # Retrieve variable & command each time properties is open
        self.entry_properties_variable.set_text(self.game.get_info(InfoKey.VARIABLES))
        self.entry_properties_command.set_text(self.game.get_info(InfoKey.COMMAND))

        # Center properties window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

    def _compatibility_choice_label(self, choice):
        """Return the user-facing label for a compatibility choice."""
        if choice.choice_id == SYSTEM_WINE_CHOICE_ID:
            return _("System Wine")

        if choice.choice_id == CUSTOM_WINE_CHOICE_ID:
            return _("Custom Wine")

        if choice.source == "steam":
            return _("Steam — {}").format(choice.name)

        if choice.source == "custom":
            return _("Custom — {}").format(choice.name)

        return _("Missing — {}").format(choice.name)

    def _populate_compatibility_tools(self, preferred_choice_id=None):
        """
        Discover installed compatibility tools and populate the selector.

        Discovery happens each time Properties is opened and whenever Refresh
        is pressed. The currently configured missing Proton path is retained as
        a visible unavailable choice instead of silently reverting to Wine.
        """
        choices = build_compatibility_choices(
            selected_runner=self.game.get_info(InfoKey.WINDOWS_RUNNER),
            selected_proton_path=self.game.get_info(InfoKey.PROTON_PATH),
        )

        self._compatibility_choices = {
            choice.choice_id: choice
            for choice in choices
        }

        self.combo_properties_compatibility.remove_all()

        for choice in choices:
            self.combo_properties_compatibility.append(
                choice.choice_id,
                self._compatibility_choice_label(choice),
            )

        configured_choice_id = selected_compatibility_choice_id(
            selected_runner=self.game.get_info(InfoKey.WINDOWS_RUNNER),
            selected_proton_path=self.game.get_info(InfoKey.PROTON_PATH),
            custom_wine_path=self.game.get_info(InfoKey.CUSTOM_WINE),
            system_wine_path=shutil.which("wine") or "",
        )

        if (
            preferred_choice_id
            and preferred_choice_id in self._compatibility_choices
        ):
            active_choice_id = preferred_choice_id
        elif configured_choice_id in self._compatibility_choices:
            active_choice_id = configured_choice_id
        else:
            active_choice_id = SYSTEM_WINE_CHOICE_ID

        self.combo_properties_compatibility.set_active_id(
            active_choice_id
        )

        self._update_compatibility_controls()

    def _selected_compatibility_choice(self):
        choice_id = self.combo_properties_compatibility.get_active_id()

        return self._compatibility_choices.get(choice_id)

    def _update_compatibility_controls(self):
        """
        Update compatibility status and show only controls relevant to the
        selected backend.
        """
        choice = self._selected_compatibility_choice()

        if not choice:
            return

        is_custom_wine = (
            choice.choice_id == CUSTOM_WINE_CHOICE_ID
        )
        is_proton = choice.choice_id.startswith(
            PROTON_CHOICE_PREFIX
        )
        show_custom_wine = (
            self.game.platform == "windows"
            and is_custom_wine
        )

        self._update_umu_controls(is_proton)

        # Proton is a peer backend, not a wrapper around the host Wine binary.
        # Do not leave Custom Wine controls visible while Proton is selected.
        self.label_wine_custom.set_visible(show_custom_wine)
        self.button_properties_wine.set_visible(show_custom_wine)
        self.button_properties_reset.set_visible(show_custom_wine)
        self.button_properties_wine.set_sensitive(show_custom_wine)
        self.button_properties_reset.set_sensitive(show_custom_wine)

        # The existing Winetricks button invokes the host winetricks binary
        # directly and is not Proton-aware.
        if self.game.is_installed():
            self.button_properties_winetricks.set_sensitive(
                not is_proton
            )

        if is_proton:
            self.label_properties_compatibility_path_title.set_text(
                _("Proton path:")
            )
            display_path = choice.path

            if not choice.available:
                display_path = _("Missing: {}").format(
                    choice.path
                )

            tooltip_text = _(
                "{}\nThis Proton build is used through UMU and the "
                "Steam Linux Runtime for both installation and launch."
            ).format(display_path)

        elif is_custom_wine:
            self.label_properties_compatibility_path_title.set_text(
                _("Wine path:")
            )
            display_path = (
                self.button_properties_wine.get_filename()
                or _("No Wine executable selected")
            )
            tooltip_text = display_path

        else:
            self.label_properties_compatibility_path_title.set_text(
                _("Wine path:")
            )
            display_path = (
                shutil.which("wine")
                or _("System Wine executable not found")
            )
            tooltip_text = display_path

        self.label_properties_compatibility_path.set_text(
            display_path
        )
        self.label_properties_compatibility_path.set_tooltip_text(
            tooltip_text
        )

    def _update_umu_controls(self, is_proton):
        """Show UMU runtime status only for Proton compatibility backends."""
        show_runtime = (
            self.game.platform == "windows"
            and is_proton
        )

        self.label_properties_umu_runtime_title.set_visible(
            show_runtime
        )
        self.label_properties_umu_runtime.set_visible(
            show_runtime
        )

        if not show_runtime:
            self.button_properties_umu_install.hide()
            return

        status = get_umu_status()

        if status and status.compatible:
            runtime_text = _(
                "UMU Launcher {} ✓"
            ).format(status.version_text)
            tooltip_text = _(
                "Using {}\nUMU {} or newer is required for Proton."
            ).format(
                status.path,
                MINIMUM_UMU_VERSION_TEXT,
            )
            self.button_properties_umu_install.hide()

        elif status:
            runtime_text = _(
                "UMU Launcher {} — update required"
            ).format(status.version_text)
            tooltip_text = _(
                "{}\nMiniGalaxy requires UMU {} or newer for Proton."
            ).format(
                status.path,
                MINIMUM_UMU_VERSION_TEXT,
            )
            self.button_properties_umu_install.set_label(
                _("Update UMU")
            )
            self.button_properties_umu_install.show()

        else:
            runtime_text = _(
                "UMU Launcher not installed"
            )
            tooltip_text = _(
                "MiniGalaxy requires UMU {} or newer for Proton and can "
                "install a verified user-level copy automatically."
            ).format(MINIMUM_UMU_VERSION_TEXT)
            self.button_properties_umu_install.set_label(
                _("Install UMU")
            )
            self.button_properties_umu_install.show()

        self.label_properties_umu_runtime.set_text(
            runtime_text
        )
        self.label_properties_umu_runtime.set_tooltip_text(
            tooltip_text
        )

    def _ensure_umu_available(self):
        """
        Ensure Proton has a compatible UMU runtime before saving selection.

        This is intentionally user-level and distro-independent: MiniGalaxy
        downloads its pinned, checksum-verified upstream standalone zipapp.
        """
        status = get_umu_status()

        if status and status.compatible:
            return True

        try:
            install_managed_umu()
        except UmuInstallError as error:
            self.parent_window.show_error(str(error))
            self._update_umu_controls(True)
            return False

        self._update_umu_controls(True)
        return True

    def _save_compatibility_selection(self):
        """
        Persist the selected Windows compatibility tool for this game.

        This runs even for games which are not installed yet because the
        compatibility choice must be available to the installer.
        """
        if self.game.platform != "windows":
            return True

        choice = self._selected_compatibility_choice()

        if not choice:
            self.parent_window.show_error(
                _("No compatibility tool is selected.")
            )
            return False

        if choice.choice_id == SYSTEM_WINE_CHOICE_ID:
            self.game.set_info(InfoKey.WINDOWS_RUNNER, "")
            self.game.set_info(InfoKey.PROTON_PATH, "")
            self.game.set_info(InfoKey.CUSTOM_WINE, "")

            return True

        if choice.choice_id == CUSTOM_WINE_CHOICE_ID:
            custom_wine_path = (
                self.button_properties_wine.get_filename()
            )

            if not custom_wine_path:
                self.parent_window.show_error(
                    _(
                        "Select a Wine executable before "
                        "using Custom Wine."
                    )
                )
                return False

            self.game.set_info(InfoKey.WINDOWS_RUNNER, "")
            self.game.set_info(InfoKey.PROTON_PATH, "")
            self.game.set_info(
                InfoKey.CUSTOM_WINE,
                str(custom_wine_path),
            )

            return True

        if choice.choice_id.startswith(PROTON_CHOICE_PREFIX):
            if not self._ensure_umu_available():
                return False

            self.game.set_info(
                InfoKey.WINDOWS_RUNNER,
                "proton",
            )
            self.game.set_info(
                InfoKey.PROTON_PATH,
                choice.path,
            )

            # Preserve any previously configured Custom Wine path. It is
            # ignored while Proton is selected but remains available if the
            # user later switches this game back to Custom Wine.
            return True

        self.parent_window.show_error(
            _("The selected compatibility tool is invalid.")
        )

        return False

    def _on_compatibility_changed(self, widget):
        self._update_compatibility_controls()

    def _on_compatibility_refresh(self, button):
        current_choice_id = (
            self.combo_properties_compatibility.get_active_id()
        )

        self._populate_compatibility_tools(
            preferred_choice_id=current_choice_id,
        )

    def _on_umu_install(self, button):
        self._ensure_umu_available()

    def _on_custom_wine_file_set(self, button):
        if (
            self.combo_properties_compatibility.get_active_id()
            == CUSTOM_WINE_CHOICE_ID
        ):
            self._update_compatibility_controls()

    @Gtk.Template.Callback("on_button_properties_cancel_clicked")
    def cancel_pressed(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_ok_clicked")
    def ok_pressed(self, button):
        game_installed = self.game.is_installed()

        if not self._save_compatibility_selection():
            return

        if game_installed:
            self.game.set_info(InfoKey.CHECK_UPDATES, self.switch_properties_check_for_updates.get_active())
            self.game.set_info(InfoKey.SHOW_FPS, self.switch_properties_show_fps.get_active())
            if self.switch_properties_use_gamemode.get_active() and not shutil.which("gamemoderun"):
                self.parent_window.show_error(_("GameMode wasn't found. Using GameMode cannot be enabled."))
                self.game.set_info(InfoKey.GAMEMODE, False)
            else:
                self.game.set_info(InfoKey.GAMEMODE, self.switch_properties_use_gamemode.get_active())
            if self.switch_properties_use_mangohud.get_active() and not shutil.which("mangohud"):
                self.parent_window.show_error(_("MangoHud wasn't found. Using MangoHud cannot be enabled."))
                self.game.set_info(InfoKey.MANGOHUD, False)
            else:
                self.game.set_info(InfoKey.MANGOHUD, self.switch_properties_use_mangohud.get_active())
            self.game.set_info(InfoKey.VARIABLES, str(self.entry_properties_variable.get_text()))
            self.game.set_info(InfoKey.COMMAND, str(self.entry_properties_command.get_text()))

        self.game.set_info(InfoKey.HIDE_GAME, self.switch_properties_hide_game.get_active())
        self.parent_library.filter_library()

        if game_installed and self.config.create_applications_file:
            create_applications_file(game=self.game, override=True)

        self.destroy()

    @Gtk.Template.Callback("on_button_properties_regedit_clicked")
    def on_menu_button_regedit(self, widget):
        error_message = regedit_game(self.game)
        if error_message:
            self.parent_window.show_error(error_message)

    @Gtk.Template.Callback("on_button_properties_reset_clicked")
    def on_menu_button_reset(self, widget):
        system_wine = shutil.which("wine")

        if system_wine:
            self.button_properties_wine.set_filename(system_wine)

        self.combo_properties_compatibility.set_active_id(
            SYSTEM_WINE_CHOICE_ID
        )
        self._update_compatibility_controls()

    @Gtk.Template.Callback("on_button_properties_winecfg_clicked")
    def on_menu_button_winecfg(self, widget):
        error_message = config_game(self.game)
        if error_message:
            self.parent_window.show_error(error_message)

    @Gtk.Template.Callback("on_button_properties_winetricks_clicked")
    def on_menu_button_winetricks(self, widget):
        if not shutil.which("winetricks"):
            self.parent_window.show_error(_("Winetricks wasn't found and cannot be used."))
        else:
            winetricks_game(self.game)

    @Gtk.Template.Callback("on_button_properties_open_files_clicked")
    def on_menu_button_open_files(self, widget):
        subprocess.call(["xdg-open", self.game.install_dir])

    def button_sensitive(self, game):
        if not game.is_installed():
            self.button_properties_open_files.set_sensitive(False)
            self.button_properties_regedit.set_sensitive(False)
            self.button_properties_winecfg.set_sensitive(False)
            self.button_properties_winetricks.set_sensitive(False)
            self.button_properties_open_files.set_sensitive(False)
            self.switch_properties_check_for_updates.set_sensitive(False)
            self.switch_properties_show_fps.set_sensitive(False)
            self.switch_properties_use_gamemode.set_sensitive(False)
            self.switch_properties_use_mangohud.set_sensitive(False)
            self.entry_properties_variable.set_sensitive(False)
            self.entry_properties_command.set_sensitive(False)

        if game.platform == 'linux':
            self.label_properties_compatibility_tool.hide()
            self.combo_properties_compatibility.hide()
            self.label_properties_compatibility_path_title.hide()
            self.label_properties_compatibility_path.hide()
            self.button_properties_compatibility_refresh.hide()
            self.label_properties_umu_runtime_title.hide()
            self.label_properties_umu_runtime.hide()
            self.button_properties_umu_install.hide()
            self.button_properties_regedit.hide()
            self.button_properties_winecfg.hide()
            self.button_properties_winetricks.hide()
            self.button_properties_wine.hide()
            self.button_properties_reset.hide()
            self.label_wine_custom.hide()
        elif game.platform == 'windows':
            self.combo_properties_compatibility.set_sensitive(True)
            self.button_properties_compatibility_refresh.set_sensitive(True)
            self.button_properties_wine.set_sensitive(True)
            self.button_properties_reset.set_sensitive(True)
