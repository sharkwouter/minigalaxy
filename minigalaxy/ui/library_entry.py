import os
import re
import shutil
import threading
import urllib.parse

from minigalaxy.api import NoDownloadLinkFound
from minigalaxy.download import Download, DownloadType
from minigalaxy.download_manager import DownloadState
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.installer import uninstall_game, install_game, check_diskspace, InstallerInventory
from minigalaxy.launcher import start_game
from minigalaxy.logger import logger
from minigalaxy.paths import CACHE_DIR, DOWNLOAD_DIR, ICON_WINE_PATH, THUMBNAIL_DIR
from minigalaxy.translation import _
from minigalaxy.ui.gtk import Gtk, GLib, Notify
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
        self.predownload_state = None  # helper used to correctly reset ui states

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
        self.thumbnail_loaded = False

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

    # Downloads if Minigalaxy was closed with this game downloading
    def resume_download_if_expected(self):
        download_ids = self.config.current_downloads
        if self.game.id in download_ids:
            download_thread = threading.Thread(target=self.__download_game)
            download_thread.start()

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

    def run_primary_action(self, widget) -> None:
        """Depending on current_state, this will (download and) install OR start the game"""
        dont_act_in_states = [State.QUEUED, State.DOWNLOADING, State.INSTALLING, State.UNINSTALLING]
        err_msg = ""
        if self.current_state in dont_act_in_states:
            pass
        elif self.current_state in [State.INSTALLED, State.UPDATABLE]:
            err_msg = start_game(self.game)
        elif self.current_state == State.INSTALLABLE:
            install_thread = threading.Thread(target=self.__install_game, args=(self.get_keep_executable_path(),))
            install_thread.start()
        elif self.current_state == State.DOWNLOADABLE:
            download_thread = threading.Thread(target=self.__download_game)
            download_thread.start()
        if err_msg:
            self.parent_window.show_error(_("Failed to start {}:").format(self.game.name), err_msg)

    def confirm_and_cancel_download(self, widget=None, download_list=None):
        question = _("Are you sure you want to cancel downloading {}?").format(self.game.name)
        if self.parent_window.show_question(question):
            self.prevent_resume_on_startup()
            if not download_list:
                download_list = [*self.download_list]  # use copy or feedback from download_manager will change the list

            if not download_list:  # Safety measure. DownloadManager will cancel ALL active when empty is passed
                return
            self.download_manager.cancel_download(download_list)
            for d in download_list:
                if d.cancel_reason:
                    continue

                # download has finished regularly (no cancel reason), so it won't receive cancel from download manager
                # manually call the cancel() callback
                d.cancel()
            # second round to support parallel downloads:
            # expect multiple executables and try to delete inventory for each of them
            for d in download_list:
                if LibraryEntry.is_executable(d.save_location):
                    inventory = InstallerInventory.from_file_system(d.save_location)
                    inventory.delete_files()

    def confirm_and_uninstall(self, widget):
        question = _("Are you sure you want to uninstall %s?" % self.game.name)
        if self.parent_window.show_question(question):
            uninstall_thread = threading.Thread(target=self.__uninstall_game)
            uninstall_thread.start()

    def run_update(self, widget):
        download_thread = threading.Thread(target=self.__download_update)
        download_thread.start()

    def get_keep_executable_path(self):
        keep_path = ""
        exes_by_creation_date = {}
        if os.path.isdir(self.keep_path):
            for dir_content in os.listdir(self.keep_path):
                kept_file = os.path.join(self.keep_path, dir_content)
                if LibraryEntry.is_executable(kept_file):
                    exes_by_creation_date[int(os.path.getmtime(kept_file))] = kept_file

        if exes_by_creation_date:
            ctimes_sorted = [*exes_by_creation_date.keys()]
            ctimes_sorted.sort()
            for creation_time in ctimes_sorted:
                installer = exes_by_creation_date[creation_time]
                inventory = InstallerInventory(installer)
                if inventory.is_complete():
                    return installer

        return keep_path

    @staticmethod
    def is_executable(file):
        return os.path.isfile(file) and (os.access(file, os.X_OK) or os.path.splitext(file)[-1] in [".exe", ".sh"])

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

    '''----- DOWNLOAD ACTIONS -----'''

    def __download_game(self) -> None:
        finish_func = self.__install_game
        result, download_info = self.get_download_info()
        if result:
            result = self._download(self.game.id, download_info, DownloadType.GAME, finish_func)
        if not result:
            self.update_to_state(self.predownload_state)

    def __download_update(self) -> None:
        finish_func = self.__install_update
        result, download_info = self.get_download_info(self.game.platform)
        if result:
            result = self._download(self.game.id, download_info, DownloadType.GAME_UPDATE, finish_func)
        if not result:
            self.update_to_state(self.predownload_state)

    def __download_icon(self, force=False, game_info=None):
        local_name = self.game.get_cached_icon_path()
        if os.path.exists(local_name) and not force:
            return local_name

        if self.offline:
            return

        if not game_info:
            game_info = self.api.get_info(self.game)
        icon = game_info.get('images', {}).get('icon', None)
        if not icon:
            return

        '''game_info images dict does not contain fully valid urls.
        The entries there appear to start with //'''
        icon_url = re.sub('^.*?//', 'https://', icon, count=1)
        download = Download(url=icon_url, save_location=local_name)
        self.download_manager.download_now(download)
        return local_name

    def _download(self, gog_item_id, download_info, download_type, finish_func, download_icon=None):  # noqa: C901
        # several dlc could be downloading in parallel, remember state before they started
        # only overwrite if not set already
        if not self.download_list and not self.predownload_state:
            self.predownload_state = self.current_state

        download_success = True
        self.game.set_install_dir(self.config.install_dir)
        target_download_dir = self.__determine_download_dir(download_info)
        self.update_to_state(State.QUEUED)

        if not download_icon:
            download_icon = self.__download_icon()

        # Need to update the config with DownloadType metadata
        self.config.add_ongoing_download(gog_item_id)
        # Start the download for all files
        number_of_files = len(download_info['files'])
        total_file_size = 0
        download_files = []

        download_inventory = InstallerInventory()
        callback_factory = CallbackFuncWrapper(finish_func, self.__cancel, self, download_files, download_inventory)

        for key, file_info in enumerate(download_info['files']):
            try:
                download_url = self.api.get_real_download_link(file_info["downlink"])
            except ValueError as e:
                logger.error("Error getting download URL from file_info downlink: %s", file_info["downlink"], exc_info=1)
                GLib.idle_add(self.parent_window.show_error, _("Download error"), _(str(e)))
                download_success = False
                break

            info = self.api.get_download_file_info(file_info["downlink"])
            total_file_size += info.size
            # Extract the filename from the download url
            filename = urllib.parse.unquote(urllib.parse.urlsplit(download_url).path)
            filename = filename.split("/")[-1]
            download_path = os.path.join(target_download_dir, filename)
            download_inventory.set_path_once(download_path)  # assumption: first file is installer executable
            if info.md5:
                self.game.md5sum[os.path.basename(download_path)] = info.md5
            download_inventory.add_file(download_path, info)
            download = Download(
                url=download_url,
                save_location=download_path,
                download_type=download_type,
                progress_func=self.set_progress,
                number=number_of_files - key,
                out_of_amount=number_of_files,
                game=self.game,
                download_icon=download_icon
            )
            callback_factory.add_callbacks(download)
            download_files.append(download)

        self.download_list.extend(download_files)

        if download_success and check_diskspace(total_file_size, self.game.install_dir):
            # checking file size only makes sense when the real downlink has been found for all files
            download_inventory.save()
            self.download_manager.download(download_files)
        else:
            ds_msg_title = _("Download error")
            dl_name = download_info.get('name', self.game.name)
            ds_msg_text = _("Not enough disk space to install game:\n{}").format(dl_name)
            GLib.idle_add(self.parent_window.show_error, ds_msg_title, ds_msg_text)
            self.config.remove_ongoing_download(gog_item_id)
            self.reset_to_idle_state_if_possible()
            download_success = False

        return download_success

    def __determine_download_dir(self, download_info):
        download_dir = self.download_dir
        if self.config.keep_installers:
            download_dir = self.keep_path

        # DLC download go into subfolder of their own
        last_dir = os.path.basename(download_dir)  # basename to avoid issues with trailing slashes
        cleaned_name = Game.strip_string(download_info['name'], to_path=True)
        if last_dir != cleaned_name:
            download_dir = os.path.join(download_dir, cleaned_name)

        return download_dir

    '''----- END DOWNLOAD ACTIONS -----'''

    '''----- INSTALL ACTIONS -----'''

    def __install_game(self, save_location, inventory=None):
        self.game.set_install_dir(self.config.install_dir)
        install_success = self._install(self.game.id, save_location, inventory=inventory)
        if install_success:
            popup = Notify.Notification.new("Minigalaxy", _("Finished downloading and installing {}")
                                            .format(self.game.name), "dialog-information")
            popup.show()
            self.__check_for_dlc(self.api.get_info(self.game))

    def __install_update(self, save_location, inventory=None):
        install_success = self._install(self.game.id, save_location, update=True, inventory=inventory)
        if install_success:
            image_tooltip = self.game.name
            if self.game.platform == "windows":
                image_tooltip += " (Wine)"

            self.__set_image_tooltip(image_tooltip)
        # need to only check and update dlcs which are installed
        for dlc in self.dlc_dict.values():
            dlc.refresh_download_info()
            if dlc.is_update_available():
                dlc.download()

    def _install(self, gog_item_id, save_location, update=False, dlc_title="", inventory=None):
        if update:
            processing_state = State.UPDATING
        else:
            processing_state = State.INSTALLING

        self.update_to_state_if_idle(processing_state)
        err_msg = install_game(
            self.game,
            save_location,
            self.config.lang,
            self.config.install_dir,
            self.config.keep_installers,
            self.config.create_applications_file,
            installer_inventory=inventory
        )

        if not err_msg:
            self.update_to_state(State.INSTALLED)
            install_success = True
            if dlc_title:
                self.game.set_dlc_info("version", self.api.get_version(self.game, dlc_name=dlc_title), dlc_title)
            else:
                self.game.set_info("version", self.api.get_version(self.game))
            self.config.remove_ongoing_download(gog_item_id)
        else:
            GLib.idle_add(self.parent_window.show_error, _("Failed to install {}").format(self.game.name), err_msg)
            self.reset_to_idle_state_if_possible()
            install_success = False
        return install_success

    def __uninstall_game(self):
        self.update_to_state(State.UNINSTALLING)
        uninstall_game(self.game)
        self.update_to_state(State.DOWNLOADABLE)
        GLib.idle_add(self.reload_state)

    '''----- END INSTALL ACTIONS -----'''

    def __cancel(self, item_list=None):
        items_to_clear = item_list if item_list else [*self.download_list]
        for item in items_to_clear:
            if item in self.download_list:
                self.download_list.remove(item)

        # only cancel state if no more active downloads
        self.reset_to_idle_state_if_possible()

    '''----- UPDATE CHECK HELPERS -----'''

    def _check_for_update_dlc(self):
        if self.game.is_installed() and self.game.id and not self.offline:
            game_info = self.api.get_info(self.game)
            self.__download_icon(game_info=game_info)
            if self.game.get_info("check_for_updates", True):
                game_version = self.api.get_version(self.game, gameinfo=game_info)
                update_available = self.game.is_update_available(game_version)
                if update_available:
                    self.update_to_state(State.UPDATABLE)
            self.__check_for_dlc(game_info)
        if self.offline:
            GLib.idle_add(self.menu_button_dlc.hide)

    def __check_for_dlc(self, game_info):
        dlcs = game_info["expanded_dlcs"]
        for dlc in dlcs:
            if dlc["is_installable"] and dlc["id"] in self.parent_library.owned_products_ids:
                GLib.idle_add(self.update_gtk_box_for_dlc, dlc)
                if dlc not in self.game.dlcs:
                    self.game.dlcs.append(dlc)
        if self.game.dlcs:
            GLib.idle_add(self.menu_button_dlc.show)

    '''----- END UPDATE CHECK HELPERS -----'''

    '''----- UI REPRESENTATION UTILITIES -----'''

    def recalc_dlc_list_size(self, scrollable_window, dlc_flowbox):
        """Adjusts the DLC list size when the DLC button is clicked.
        Must be called from child class instances where needed.

        Algorithm:
        1. Take half window height and divide by dlc item height.
        2. Set result as max items per column
        3. DLC list will open more columns horizontally as needed
        4. Configure fixed with for scrollable container to be 80% of window

        => This results in a table-like layout of all DLCs at roughly the size [window_width * 0.8, window_height / 2]
        """

        max_height = int(self.parent_window.get_allocated_height() / 2)
        max_width = int(self.parent_window.get_allocated_width() * 0.8)
        first_dlc = dlc_flowbox.get_child_at_index(0)
        item_height = first_dlc.get_preferred_height()[1]
        num_vertical_items = int(max_height / item_height)

        dlc_flowbox.set_max_children_per_line(num_vertical_items)
        preferred_width = dlc_flowbox.get_preferred_width()[1]
        scrollable_window.set_size_request(min(preferred_width, max_width), dlc_flowbox.get_preferred_height()[1])

    def update_gtk_box_for_dlc(self, dlc_info):
        title = dlc_info['title']
        if title not in self.dlc_dict:
            self.dlc_dict[title] = DlcListEntry(self, dlc_info)

        dlc_box = self.dlc_dict[title]
        dlc_box.refresh_state(dlc_info=dlc_info)
        dlc_box.resume_download_if_expected()

    def load_thumbnail(self):
        """
        Tries to load a thumbnail for its game.
        When a thumbnail has been loaded before, it won't be done again.
        """
        if self.thumbnail_loaded:
            return

        thumbnail_file = self.game.get_thumbnail_path()
        if self.__set_image(thumbnail_file):
            return

        if self.parent_library.offline or not self.game.image_url or not self.game.id:
            return

        # Download the thumbnail
        image_url = "https:{}_196.jpg".format(self.game.image_url)
        download = Download(image_url, thumbnail_file, DownloadType.THUMBNAIL, finish_func=self.__set_image)
        self.download_manager.download_now(download)

        return

    def __set_image(self, thumbnail_file):
        if not os.path.isfile(thumbnail_file):
            return False

        if self.game.is_installed() and THUMBNAIL_DIR == os.path.dirname(thumbnail_file):
            thumbnail_install_dir = self.game.get_thumbnail_path(use_fallback=False)
            shutil.copy2(thumbnail_file, thumbnail_install_dir)
            thumbnail_file = thumbnail_install_dir

        self.thumbnail_loaded = True
        GLib.idle_add(self.image.set_from_file, thumbnail_file)
        return True

    def __set_image_tooltip(self, text):
        GLib.idle_add(self.image.set_tooltip_text, text)

    '''----- END UI REPRESENTATION UTILITIES -----'''

    '''----- STATE HANDLING -----'''

    def set_progress(self, percentage: int):
        if self.current_state in [State.QUEUED, State.INSTALLED]:
            self.update_to_state(State.DOWNLOADING)
        if self.progress_bar:
            GLib.idle_add(self.progress_bar.set_fraction, percentage / 100)
            GLib.idle_add(self.progress_bar.set_tooltip_text, "{}%".format(percentage))

    def reload_state(self):
        self.game.set_install_dir(self.config.install_dir)
        dont_act_in_states = [State.QUEUED, State.DOWNLOADING, State.INSTALLING, State.UNINSTALLING,
                              State.UPDATING]
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
        # The user must have the possibility to access
        # to the store button even if the game is not installed
        self.menu_button.show()
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
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
            GLib.idle_add(self.STATE_UPDATE_HANDLERS[state])

    def update_to_state_if_idle(self, state):
        """Move to the given state, but only when there is no more ongoing download/install"""
        if self.predownload_state and self.download_list:
            return
        self.update_to_state(state)

    def reset_to_idle_state_if_possible(self):
        """
        Go back to the state before download/installation was started, but only if nothing is ongoing anymore.
        Relevant when several DLC are downloaded in parallel. Going back to idle only happens when all are done.
        Relies on self.predownload_state which will be set whenever the first download starts.
        It will take whatever state the element had before, which will be one of the following:
        - DOWNLOADABLE
        - UPDATEABLE
        - INSTALLED
        """
        if self.predownload_state and not self.download_list:
            self.update_to_state(self.predownload_state)
            self.predownload_state = None
            GLib.idle_add(self.reload_state)

    '''----- END STATE HANDLING -----'''


class CallbackFuncWrapper:
    def __init__(self, finish_func, cancel_func, lib_entry, download_files, installer_inventory=None):
        self.lib_entry = lib_entry
        # empty or incomplete at construction time, must be evaluated when finish_func is called
        self.download_files = download_files
        self.finished_downloads = {}
        self.callback_finish = finish_func
        self.callback_cancel = cancel_func
        self.require_confirmation = True  # for cancel
        self.inventory = installer_inventory

    def finish_func(self, save_location):
        self.finished_downloads[save_location] = 1
        if sum(self.finished_downloads.values()) != len(self.download_files):
            return

        self.remove_from_download_list()

        save_locations = []
        for d in self.download_files:
            save_locations.append(d.save_location)

        self.callback_finish(self.download_files[0].save_location, inventory=self.inventory)

    def cancel_func(self, trigger):
        item_id = self.lib_entry.game.id
        if item_id not in self.lib_entry.config.current_downloads:
            # trigger for cancel was cancel button on GameTile
            self.require_confirmation = False

        self.callback_cancel(item_list=[trigger])
        if trigger.cancel_reason is DownloadState.CANCELED and self.require_confirmation:
            self.require_confirmation = False
            GLib.idle_add(self.lib_entry.confirm_and_cancel_download, None, self.download_files)

    def remove_from_download_list(self):
        for download in self.download_files:
            if download in self.lib_entry.download_list:
                self.lib_entry.download_list.remove(download)

    def add_callbacks(self, download):
        handler_instance = self
        download.on_cancel(lambda: handler_instance.cancel_func(download))
        if self.callback_finish:
            download.on_finish(self.finish_func)


class DlcListEntry(Gtk.Box):
    def __init__(self, parent_entry, dlc_info):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.parent_entry = parent_entry

        self.dlc_id = dlc_info['id']
        self.dlc_info = dlc_info
        self.dlc_icon_path = None
        self.set_spacing(8)

        self.icon_image = Gtk.Image()
        self.icon_image.set_from_icon_name("media-optical", Gtk.IconSize.BUTTON)
        self.pack_start(self.icon_image, False, True, 0)

        label = Gtk.Label(label=self.title, xalign=0)
        self.pack_start(label, True, True, 0)

        self.install_button_image = Gtk.Image()
        self.install_button = Gtk.Button()
        self.install_button.set_image(self.install_button_image)
        self.install_button.connect("clicked", self.download)
        self.pack_start(self.install_button, False, True, 0)

        parent_entry.dlc_horizontal_box.add(self)
        self.show_all()
        self.get_async_image_dlc_icon(dlc_info['id'], dlc_info["images"]["sidebarIcon"])

    @property
    def title(self) -> str:
        return self.dlc_info['title']

    @property
    def game(self):
        return self.parent_entry.game

    @property
    def api(self):
        return self.parent_entry.api

    def refresh_state(self, dlc_info=None):
        self.refresh_download_info(dlc_info)
        installable = True
        if self.is_update_available():
            icon_name = "emblem-synchronizing"
            installable = True
        elif self.game.is_installed(dlc_title=self.title):
            icon_name = "object-select"
            installable = False
        else:
            icon_name = "document-save"

        self.__set_button_state(installable and not self.is_installing(), icon_name)

    def get_async_image_dlc_icon(self, dlc_id, icon):
        self.dlc_icon_path = self.parent_entry.game.get_cached_icon_path(dlc_id)
        if os.path.isfile(self.dlc_icon_path):
            self.__set_downloaded_dlc_icon(self.dlc_icon_path)

        elif icon:
            download = Download(
                url="http:{}".format(icon),
                save_location=self.dlc_icon_path,
                finish_func=self.__set_downloaded_dlc_icon
            )
            self.parent_entry.download_manager.download_now(download)

    def resume_download_if_expected(self):
        if self.parent_entry.current_state not in [State.INSTALLED, State.UPDATABLE, State.UPDATE_INSTALLABLE]:
            return

        if self.dlc_id in self.parent_entry.config.current_downloads:
            self.download()

    def download(self, *args):  # Ignore other args. Allows usage as click handler.
        self.__set_button_state(False)
        threading.Thread(target=self.__run_download).start()

    def install(self, save_location, inventory=None):
        install_success = self.parent_entry._install(self.dlc_id, save_location, dlc_title=self.title, inventory=inventory)
        if not install_success:
            self.parent_entry.update_to_state(self.parent_entry.predownload_state)
        self.parent_entry._check_for_update_dlc()

    def is_update_available(self):
        version = self.dlc_installer["version"]
        return self.game.is_update_available(version_from_api=version, dlc_title=self.title)

    def is_installing(self):
        return self.dlc_id in self.parent_entry.config.current_downloads

    def refresh_download_info(self, info=None):
        if not info:
            info = self.api.get_dlc_info(self.game, self.dlc_id)
        self.dlc_info = info
        self.dlc_installer = self.api.get_download_info(self.game, dlc_installers=info["downloads"]["installers"])

    def __run_download(self):
        result = self.parent_entry._download(self.dlc_id,
                                             self.dlc_installer,
                                             DownloadType.GAME_DLC,
                                             self.install,
                                             download_icon=self.dlc_icon_path)
        if not result:
            self.parent_entry.update_to_state(self.parent_entry.predownload_state)

    def __set_downloaded_dlc_icon(self, save_location):
        GLib.idle_add(self.icon_image.set_from_file, save_location)

    def __set_button_state(self, sensitive, icon_name=None):
        GLib.idle_add(self.install_button.set_sensitive, sensitive)
        if icon_name:
            GLib.idle_add(self.install_button_image.set_from_icon_name, icon_name, Gtk.IconSize.BUTTON)
