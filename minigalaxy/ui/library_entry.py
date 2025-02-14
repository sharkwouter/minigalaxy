import os
import threading

from minigalaxy.api import NoDownloadLinkFound
from minigalaxy.download import Download
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.logger import logger
from minigalaxy.paths import CACHE_DIR, DOWNLOAD_DIR, ICON_DIR, ICON_WINE_PATH
from minigalaxy.translation import _
from minigalaxy.ui.gtk import GLib, Gtk
from minigalaxy.ui.information import Information
from minigalaxy.ui.properties import Properties


class LibraryEntry:
    '''encapsulates all actions that can be taken for an individual game'''

    def __init__(self, parent_library, game: Game):
        self.parent_library = parent_library
        self.parent_window = parent_library.parent_window

        self.api = parent_library.api
        self.config = parent_library.config
        self.download_manager = parent_library.download_manager
        self.game = game

        self.offline = parent_library.offline
        self.thumbnail_set = False
        self.download_list = []
        self.dlc_dict = {}
        self.current_state = State.DOWNLOADABLE

        # Set folder for download installer
        self.download_dir = os.path.join(DOWNLOAD_DIR, self.game.get_install_directory_name())

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(self.config.install_dir, "installer")
        self.keep_path = os.path.join(self.keep_dir, self.game.get_install_directory_name())
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, mode=0o755)

        self.STATE_UPDATE_HANDLERS = {
            State.DOWNLOADABLE: self.state_downloadable,
            State.INSTALLABLE: self.state_installable,
            State.QUEUED: self.state_queued,
            State.DOWNLOADING: self.state_downloading,
            State.INSTALLING: self.state_installing,
            State.INSTALLED: self.state_installed,
            State.UNINSTALLING: self.state_uninstalling,
            State.UPDATABLE: self.state_updatable,
            State.UPDATING: self.state_updating,
        }

    def init_ui_elements(self):
        self.image.set_tooltip_text(self.game.name)
        self.reload_state()
        load_thumbnail_thread = threading.Thread(target=self.load_thumbnail)
        load_thumbnail_thread.start()

        # Icon for Windows games
        if self.game.platform == "windows":
            self.image.set_tooltip_text("{} (Wine)".format(self.game.name))
            self.wine_icon.set_from_file(ICON_WINE_PATH)
            self.wine_icon.show()

    # Do not restart the download if Minigalaxy is restarted
    def prevent_resume_on_startup(self):
        self.config.remove_ongoing_download(self.game.id)

    def show_information(self, button):
        information_window = Information(self.parent_window, self.game, self.config, self.api, self.download_manager)
        information_window.run()
        information_window.destroy()

    def show_properties(self, button):
        properties_window = Properties(self.parent_library, self.game, self.config, self.api)
        properties_window.run()
        properties_window.destroy()

    def get_keep_executable_path(self):
        keep_path = ""
        if os.path.isdir(self.keep_path):
            for dir_content in os.listdir(self.keep_path):
                kept_file = os.path.join(self.keep_path, dir_content)
                if os.access(kept_file, os.X_OK) or os.path.splitext(kept_file)[-1] in [".exe", ".sh"]:
                    keep_path = kept_file
                    break
        return keep_path

    def get_download_info(self, platform="linux"):
        try:
            download_info = self.api.get_download_info(self.game, platform)
            result = True
        except NoDownloadLinkFound as e:
            logger.error("No download link found", exc_info=1)
            self.config.remove_ongoing_download(self.game.id)
            GLib.idle_add(self.parent_window.show_error, _("Download error"),
                          _("There was an error when trying to fetch the download link!\n{}".format(e)))
            download_info = False
            result = False
        return result, download_info

    def _check_for_update_dlc(self):
        if self.game.is_installed() and self.game.id and not self.offline:
            game_info = self.api.get_info(self.game)
            if self.game.get_info("check_for_updates") == "":
                self.game.set_info("check_for_updates", True)
            if self.game.get_info("check_for_updates"):
                game_version = self.api.get_version(self.game, gameinfo=game_info)
                update_available = self.game.is_update_available(game_version)
                if update_available:
                    GLib.idle_add(self.update_to_state, State.UPDATABLE)
            self._check_for_dlc(game_info)
        if self.offline:
            GLib.idle_add(self.menu_button_dlc.hide)

    def _check_for_dlc(self, game_info):
        dlcs = game_info["expanded_dlcs"]
        for dlc in dlcs:
            if dlc["is_installable"] and dlc["id"] in self.parent_library.owned_products_ids:
                d_id = dlc["id"]
                d_installer = dlc["downloads"]["installers"]
                d_icon = dlc["images"]["sidebarIcon"]
                d_name = dlc["title"]
                GLib.idle_add(self.update_gtk_box_for_dlc, d_id, d_icon, d_name, d_installer)
                if dlc not in self.game.dlcs:
                    self.game.dlcs.append(dlc)
        if self.game.dlcs:
            GLib.idle_add(self.menu_button_dlc.show)

    def get_async_image_dlc_icon(self, dlc_id, image, icon, title):
        dlc_icon_path = os.path.join(ICON_DIR, "{}.jpg".format(dlc_id))
        if icon:
            if os.path.isfile(dlc_icon_path):
                GLib.idle_add(image.set_from_file, dlc_icon_path)
            else:
                url = "http:{}".format(icon)
                dlc_icon = os.path.join(ICON_DIR, "{}.jpg".format(dlc_id))
                download = Download(url, dlc_icon)
                self.download_manager.download_now(download)
                GLib.idle_add(image.set_from_file, dlc_icon_path)

    def set_progress(self, percentage: int):
        if self.current_state in [State.QUEUED, State.INSTALLED]:
            GLib.idle_add(self.update_to_state, State.DOWNLOADING)
        if self.progress_bar:
            GLib.idle_add(self.progress_bar.set_fraction, percentage / 100)
            GLib.idle_add(self.progress_bar.set_tooltip_text, "{}%".format(percentage))

    def reload_state(self):
        self.game.set_install_dir(self.config.install_dir)
        dont_act_in_states = [State.QUEUED, State.DOWNLOADING, State.INSTALLING, State.UNINSTALLING,
                              State.UPDATING, State.DOWNLOADING]
        if self.current_state in dont_act_in_states:
            return
        if self.game.is_installed():
            self.update_to_state(State.INSTALLED)
            check_update_thread = threading.Thread(target=self._check_for_update_dlc)
            check_update_thread.start()
        elif self.get_keep_executable_path():
            self.update_to_state(State.INSTALLABLE)
        else:
            self.update_to_state(State.DOWNLOADABLE)

    def state_downloadable(self):
        self.button.set_label(_("Download"))
        self.button.set_tooltip_text(_("Download and install the game"))
        self.button.set_sensitive(True)
        self.image.set_sensitive(False)

        # The user must have the possibility to access
        # to the store button even if the game is not installed
        self.menu_button.show()
        self.menu_button.set_tooltip_text(_("Show game options menu"))
        self.menu_button_update.hide()
        self.menu_button_dlc.hide()
        self.menu_button_uninstall.hide()
        self.button_cancel.hide()
        self.progress_bar.hide()

        self.game.install_dir = ""

    def state_installable(self):
        self.button.set_label(_("Install"))
        self.button.set_tooltip_text(_("Install the game"))
        self.button.set_sensitive(True)
        self.image.set_sensitive(False)
        self.menu_button.hide()
        self.button_cancel.hide()
        self.progress_bar.hide()

        self.game.install_dir = ""

    def state_queued(self):
        self.button.set_label(_("In queue…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.show()
        self.progress_bar.show()

    def state_downloading(self):
        self.button.set_label(_("Downloading…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.show()
        self.progress_bar.show()

    def state_installing(self):
        self.button.set_label(_("Installing…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(True)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.hide()
        self.progress_bar.hide()

        self.game.set_install_dir(self.config.install_dir)
        self.parent_library.filter_library()

    def state_installed(self):
        self.button.set_label(_("Play"))
        self.button.set_tooltip_text(_("Launch the game"))
        self.button.get_style_context().add_class("suggested-action")
        self.menu_button.get_style_context().add_class("suggested-action")
        self.button.set_sensitive(True)
        self.image.set_sensitive(True)
        self.menu_button.set_tooltip_text(_("Show game options menu"))
        self.menu_button.show()
        self.menu_button_uninstall.show()
        self.button_cancel.hide()
        self.progress_bar.hide()
        self.menu_button_update.hide()
        self.update_icon.hide()

        self.game.set_install_dir(self.config.install_dir)

    def state_uninstalling(self):
        self.button.set_label(_("Uninstalling…"))
        self.button.get_style_context().remove_class("suggested-action")
        self.menu_button.get_style_context().remove_class("suggested-action")
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button.hide()
        self.button_cancel.hide()

        self.game.install_dir = ""
        self.parent_library.filter_library()

    def state_updatable(self):
        self.update_icon.show()
        self.update_icon.set_from_icon_name("emblem-synchronizing", Gtk.IconSize.LARGE_TOOLBAR)
        self.button.set_label(_("Play"))
        self.menu_button.show()
        tooltip_text = "{} (update{})".format(self.game.name, ", Wine" if self.game.platform == "windows" else "")
        self.image.set_tooltip_text(tooltip_text)
        self.menu_button_update.show()
        if self.game.platform == "windows":
            self.wine_icon.set_margin_left(22)

    def state_updating(self):
        self.button.set_label(_("Updating…"))

    def update_to_state(self, state):
        self.current_state = state
        if state in self.STATE_UPDATE_HANDLERS:
            self.STATE_UPDATE_HANDLERS[state]()
