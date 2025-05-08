import os
import re
import shutil
import threading
import time
import urllib.parse

from minigalaxy.api import NoDownloadLinkFound
from minigalaxy.download import Download, DownloadType
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.installer import uninstall_game, install_game, check_diskspace
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

    # Downloads if Minigalaxy was closed with this game downloading
    def resume_download_if_expected(self):
        download_ids = self.config.current_downloads
        if self.game.id in download_ids and self.current_state == State.DOWNLOADABLE:
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
        '''Depending on current_state, this will (download and) install OR start the game'''
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

    def confirm_and_cancel_download(self, widget):
        question = _("Are you sure you want to cancel downloading {}?").format(self.game.name)
        if self.parent_window.show_question(question):
            self.prevent_resume_on_startup()
            self.download_manager.cancel_download(self.download_list)
            try:
                for filename in os.listdir(self.download_dir):
                    if self.game.get_install_directory_name() in filename:
                        os.remove(os.path.join(self.download_dir, filename))
            except FileNotFoundError:
                pass

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

    '''----- DOWNLOAD ACTIONS -----'''

    def __download_game(self) -> None:
        finish_func = self.__install_game
        cancel_to_state = State.DOWNLOADABLE
        result, download_info = self.get_download_info()
        if result:
            result = self.__download(download_info, DownloadType.GAME, finish_func,
                                     cancel_to_state)
        if not result:
            self.update_to_state(cancel_to_state)

    def __download_update(self) -> None:
        finish_func = self.__install_update
        cancel_to_state = State.UPDATABLE
        result, download_info = self.get_download_info(self.game.platform)
        if result:
            result = self.__download(download_info, DownloadType.GAME_UPDATE, finish_func,
                                     cancel_to_state)
        if not result:
            self.update_to_state(cancel_to_state)

    def __download_dlc(self, dlc_installers) -> None:
        download_info = self.api.get_download_info(self.game, dlc_installers=dlc_installers)
        dlc_title = self.game.name
        dlc_icon = None
        for dlc in self.game.dlcs:
            if dlc["downloads"]["installers"] == dlc_installers:
                dlc_id = dlc.get('id', None)
                dlc_icon = self.game.get_cached_icon_path(dlc_id)
                dlc_title = dlc["title"]

        def finish_func(save_location):
            self.__install_dlc(save_location, dlc_title=dlc_title)

        cancel_to_state = State.INSTALLED
        result = self.__download(download_info, DownloadType.GAME_DLC, finish_func,
                                 cancel_to_state, download_icon=dlc_icon)
        if not result:
            self.update_to_state(cancel_to_state)

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

    def __download(self, download_info, download_type, finish_func, cancel_to_state, download_icon=None):  # noqa: C901
        download_success = True
        self.game.set_install_dir(self.config.install_dir)
        self.update_to_state(State.QUEUED)

        if not download_icon:
            download_icon = self.__download_icon()

        # Need to update the config with DownloadType metadata
        self.config.add_ongoing_download(self.game.id)
        # Start the download for all files
        self.download_list = []
        ProgressHack.unset_progress_tracker(self)
        number_of_files = len(download_info['files'])
        total_file_size = 0
        download_files = []
        self.download_finished = 0

        def finish_func_wrapper(func):

            def wrapper(*args):
                self.download_finished += 1
                if self.download_finished == number_of_files:
                    # Assume the first item in download_info['files] is the executable
                    # This item ends up last in self.download_list because it's reversed
                    finish_func(self.download_list[-1].save_location)

            if func is not None:
                return wrapper
            else:
                return None

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
            download_path = os.path.join(self.download_dir, filename)
            if info.md5:
                self.game.md5sum[os.path.basename(download_path)] = info.md5
            download = Download(
                url=download_url,
                save_location=download_path,
                download_type=download_type,
                finish_func=finish_func_wrapper(finish_func),
                game=self.game,
                download_icon=download_icon
            )
            # uses side-effects to maintain a list of progress percentages
            ProgressHack(download, self, lambda: self.__cancel(to_state=cancel_to_state))
            download_files.insert(0, download)
        self.download_list.extend(download_files)

        if check_diskspace(total_file_size, self.game.install_dir):
            self.download_manager.download(download_files)
        else:
            ds_msg_title = _("Download error")
            dl_name = download_info.get('name', self.game.name)
            ds_msg_text = _("Not enough disk space to install game:\n{}").format(dl_name)
            GLib.idle_add(self.parent_window.show_error, ds_msg_title, ds_msg_text)
            self.config.remove_ongoing_download(self.game.id)
            download_success = False

        return download_success

    '''----- END DOWNLOAD ACTIONS -----'''

    '''----- INSTALL ACTIONS -----'''

    def __install_game(self, save_location):
        self.config.remove_ongoing_download(self.game.id)
        self.download_list = []
        ProgressHack.unset_progress_tracker(self)
        self.game.set_install_dir(self.config.install_dir)
        install_success = self.__install(save_location)
        if install_success:
            popup = Notify.Notification.new("Minigalaxy", _("Finished downloading and installing {}")
                                            .format(self.game.name), "dialog-information")
            popup.show()
            self.__check_for_dlc(self.api.get_info(self.game))

    def __install_update(self, save_location):
        install_success = self.__install(save_location, update=True)
        if install_success:
            if self.game.platform == "windows":
                self.image.set_tooltip_text("{} (Wine)".format(self.game.name))
            else:
                self.image.set_tooltip_text(self.game.name)
        for dlc in self.game.dlcs:
            download_info = self.api.get_download_info(self.game, dlc_installers=dlc["downloads"]["installers"])
            if self.game.is_update_available(version_from_api=download_info["version"], dlc_title=dlc["title"]):
                self.__download_dlc(dlc["downloads"]["installers"])

    def __install_dlc(self, save_location, dlc_title):
        install_success = self.__install(save_location, dlc_title=dlc_title)
        if not install_success:
            self.update_to_state(State.INSTALLED)
        self.__check_for_update_dlc()

    def __install(self, save_location, update=False, dlc_title=""):
        if update:
            processing_state = State.UPDATING
            failed_state = State.INSTALLED
        else:
            processing_state = State.INSTALLING
            failed_state = State.DOWNLOADABLE
        success_state = State.INSTALLED
        self.update_to_state(processing_state)
        err_msg = install_game(
            self.game,
            save_location,
            self.config.lang,
            self.config.install_dir,
            self.config.keep_installers,
            self.config.create_applications_file
        )

        if not err_msg:
            self.update_to_state(success_state)
            install_success = True
            if dlc_title:
                self.game.set_dlc_info("version", self.api.get_version(self.game, dlc_name=dlc_title), dlc_title)
            else:
                self.game.set_info("version", self.api.get_version(self.game))
        else:
            GLib.idle_add(self.parent_window.show_error, _("Failed to install {}").format(self.game.name), err_msg)
            self.update_to_state(failed_state)
            install_success = False
        return install_success

    def __uninstall_game(self):
        self.update_to_state(State.UNINSTALLING)
        uninstall_game(self.game)
        self.update_to_state(State.DOWNLOADABLE)
        GLib.idle_add(self.reload_state)

    '''----- END INSTALL ACTIONS -----'''

    def __cancel(self, to_state):
        self.download_list = []
        ProgressHack.unset_progress_tracker(self)
        self.update_to_state(to_state)
        GLib.idle_add(self.reload_state)

    '''----- UPDATE CHECK HELPERS -----'''

    def __check_for_update_dlc(self):
        if self.game.is_installed() and self.game.id and not self.offline:
            game_info = self.api.get_info(self.game)
            self.__download_icon(game_info=game_info)
            if self.game.get_info("check_for_updates") == "":
                self.game.set_info("check_for_updates", True)
            if self.game.get_info("check_for_updates"):
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
        '''Adjusts the DLC list size when the DLC button is clicked.
        Must be called from child class instances where needed.

        Algorithm:
        1. Take half window height and divide by dlc item height.
        2. Set result as max items per column
        3. DLC list will open more columns horizontally as needed
        4. Configure fixed with for scrollable container to be 80% of window

        => This results in a table-like layout of all DLCs at roughly the size [window_width * 0.8, window_height / 2]
        '''

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
            self.dlc_dict[title] = DlcListEntry(self, dlc_info, self.__download_dlc)

        dlc_box = self.dlc_dict[title]
        dlc_box.refresh_state()

    def load_thumbnail(self):
        if self.__set_image(""):
            return True

        tries = 10
        performed_try = 0
        # FIXME: this should happen async and retries shall be left to download_manager!
        while performed_try < tries:
            if self.game.image_url and self.game.id:
                # Download the thumbnail
                image_url = "https:{}_196.jpg".format(self.game.image_url)
                thumbnail = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
                download = Download(image_url, thumbnail, DownloadType.THUMBNAIL,
                                    finish_func=self.__set_image)
                self.download_manager.download_now(download)
                set_result = True
                break
            performed_try += 1
            time.sleep(1)
        return set_result

    def __set_image(self, save_location):
        set_result = False
        self.game.set_install_dir(self.config.install_dir)
        thumbnail_install_dir = os.path.join(self.game.install_dir, "thumbnail.jpg")
        if os.path.isfile(thumbnail_install_dir):
            GLib.idle_add(self.image.set_from_file, thumbnail_install_dir)
            set_result = True
        elif save_location and os.path.isfile(save_location):
            GLib.idle_add(self.image.set_from_file, save_location)
            # Copy image to
            if os.path.isdir(os.path.dirname(thumbnail_install_dir)):
                shutil.copy2(save_location, thumbnail_install_dir)
            set_result = True
        thumbnail_path = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
        if os.path.isfile(thumbnail_path):
            GLib.idle_add(self.image.set_from_file, thumbnail_path)
            set_result = True
        return set_result

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
                              State.UPDATING, State.DOWNLOADING]
        if self.current_state in dont_act_in_states:
            return
        if self.game.is_installed():
            self.update_to_state(State.INSTALLED)
            check_update_thread = threading.Thread(target=self.__check_for_update_dlc)
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

    '''----- END STATE HANDLING -----'''


class ProgressHack():
    '''Temporary total progress estimation until MultiPartDownloads are fully implemented'''

    def __init__(self, download, parent, cancel_fun):
        self.download = download
        # need to post-patch progress callback because it should normally be passed to download at construction time
        download.callback_progress = self.received_progress
        download.callback_cancel = self.cancel
        self.parent = parent
        self.cancel_fun = cancel_fun
        if not self.parent.download_progress:
            self.parent.download_progress = {}
            self.parent.current_progress = 0

        self.parent.download_progress[self.download] = 0

    def received_progress(self, progress):
        '''
        rough overall progress estimate. Basically the sum of all percentages / num files
        this is rough because it does not consider file sizes at all, 
        so percentages will update very fast in the beginning when small files are downloaded, then slow down
        '''
        self.parent.download_progress[self.download] = progress
        new_progress = sum(self.parent.download_progress.values()) / len(self.parent.download_list)
        if new_progress > self.parent.current_progress:
            self.parent.set_progress(new_progress)
            self.parent.current_progress = new_progress

    def cancel(self):
        # the download might not have been started yet
        print("cancel received:", self.download)
        if self.download in self.parent.download_progress:
            del self.parent.download_progress[self.download]

        if len(self.parent.download_progress) == 0:
            self.cancel_fun()

    @staticmethod
    def unset_progress_tracker(library_entry):
        library_entry.download_progress = {}


class DlcListEntry(Gtk.Box):

    def __init__(self, parent_entry, dlc_info, dlc_download_function):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.parent_entry = parent_entry

        self.title = dlc_info['title']
        self.installer = dlc_info["downloads"]["installers"]
        self.download_function = dlc_download_function
        self.set_spacing(8)

        self.icon_image = Gtk.Image()
        self.icon_image.set_from_icon_name("media-optical", Gtk.IconSize.BUTTON)
        self.pack_start(self.icon_image, False, True, 0)

        label = Gtk.Label(label=self.title, xalign=0)
        self.pack_start(label, True, True, 0)

        self.install_button_image = Gtk.Image()
        self.install_button = Gtk.Button()
        self.install_button.set_image(self.install_button_image)
        self.install_button.connect("clicked", self.__dlc_button_clicked)
        self.pack_start(self.install_button, False, True, 0)

        parent_entry.dlc_horizontal_box.add(self)
        self.show_all()
        self.get_async_image_dlc_icon(dlc_info['id'], dlc_info["images"]["sidebarIcon"])

    def refresh_state(self):
        game = self.parent_entry.game
        download_info = self.parent_entry.api.get_download_info(game, dlc_installers=self.installer)
        if game.is_update_available(version_from_api=download_info["version"], dlc_title=self.title):
            icon_name = "emblem-synchronizing"
            self.install_button.set_sensitive(True)
        elif game.is_installed(dlc_title=self.title):
            icon_name = "object-select"
            self.install_button.set_sensitive(False)
        else:
            icon_name = "document-save"
            if self.title not in self.parent_entry.download_list:
                self.install_button.set_sensitive(True)
        self.install_button_image.set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)

    def get_async_image_dlc_icon(self, dlc_id, icon):
        self.dlc_icon_path = self.parent_entry.game.get_cached_icon_path(dlc_id)
        if os.path.isfile(self.dlc_icon_path):
            GLib.idle_add(self.icon_image.set_from_file, self.dlc_icon_path)

        elif icon:
            download = Download(
                url="http:{}".format(icon),
                save_location=self.dlc_icon_path,
                finish_func=self.__set_downloaded_dlc_icon
            )
            self.parent_entry.download_manager.download_now(download)

    def __dlc_button_clicked(self, button):
        button.set_sensitive(False)
        threading.Thread(target=self.download_function, args=(self.installer,)).start()

    def __set_downloaded_dlc_icon(self, save_location):
        GLib.idle_add(self.icon_image.set_from_file, save_location)
