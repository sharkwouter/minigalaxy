import shutil
import locale
import os
import threading
import time
import urllib.parse

from minigalaxy.config import Config
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.logger import logger
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, ICON_DIR, UI_DIR, DOWNLOAD_DIR
from minigalaxy.download import Download, DownloadType
from minigalaxy.download_manager import DownloadManager
from minigalaxy.launcher import start_game
from minigalaxy.installer import uninstall_game, install_game, check_diskspace
from minigalaxy.paths import ICON_WINE_PATH
from minigalaxy.api import NoDownloadLinkFound, Api
from minigalaxy.ui.gtk import Gtk, GLib, Notify
from minigalaxy.ui.information import Information
from minigalaxy.ui.properties import Properties


@Gtk.Template.from_file(os.path.join(UI_DIR, "gametile.ui"))
class GameTile(Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    wine_icon = Gtk.Template.Child()
    update_icon = Gtk.Template.Child()
    menu_button_update = Gtk.Template.Child()
    menu_button_dlc = Gtk.Template.Child()
    menu_button_uninstall = Gtk.Template.Child()
    dlc_horizontal_box = Gtk.Template.Child()
    menu_button_information = Gtk.Template.Child()
    menu_button_properties = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()

    def __init__(self, parent, game: Game, config: Config, api: Api, download_manager: DownloadManager):
        self.config = config
        current_locale = self.config.locale
        default_locale = locale.getdefaultlocale()[0]
        if current_locale == '':
            locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        else:
            try:
                locale.setlocale(locale.LC_ALL, (current_locale, 'UTF-8'))
            except NameError:
                locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        Gtk.Frame.__init__(self)

        self.parent = parent
        self.game = game
        self.api = api
        self.download_manager = download_manager
        self.offline = parent.offline
        self.thumbnail_set = False
        self.download_list = []
        self.dlc_dict = {}
        self.current_state = State.DOWNLOADABLE

        self.image.set_tooltip_text(self.game.name)

        # Set folder for download installer
        self.download_dir = os.path.join(DOWNLOAD_DIR, self.game.get_install_directory_name())

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(self.config.install_dir, "installer")
        self.keep_path = os.path.join(self.keep_dir, self.game.get_install_directory_name())
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, mode=0o755)

        self.reload_state()
        load_thumbnail_thread = threading.Thread(target=self.load_thumbnail)
        load_thumbnail_thread.start()

        # Start download if Minigalaxy was closed while downloading this game
        self.resume_download_if_expected()

        # Icon for Windows games
        if self.game.platform == "windows":
            self.image.set_tooltip_text("{} (Wine)".format(self.game.name))
            self.wine_icon.set_from_file(ICON_WINE_PATH)
            self.wine_icon.show()

    # Downloads if Minigalaxy was closed with this game downloading
    def resume_download_if_expected(self):
        download_ids = self.config.current_downloads
        if download_ids:
            for download_id in download_ids:
                if download_id and download_id == self.game.id and self.current_state == State.DOWNLOADABLE:
                    download_thread = threading.Thread(target=self.__download_game)
                    download_thread.start()

    # Do not restart the download if Minigalaxy is restarted
    def prevent_resume_on_startup(self):
        download_ids = self.config.current_downloads
        if download_ids:
            new_download_ids = set()
            for download_id in download_ids:
                if not (download_id and download_id == self.game.id):
                    new_download_ids.add(download_id)

            self.config.current_downloads = list(new_download_ids)

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
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
            self.parent.parent.show_error(_("Failed to start {}:").format(self.game.name), err_msg)

    @Gtk.Template.Callback("on_menu_button_information_clicked")
    def show_information(self, button):
        information_window = Information(self, self.game, self.config, self.api, self.download_manager)
        information_window.run()
        information_window.destroy()

    @Gtk.Template.Callback("on_menu_button_properties_clicked")
    def show_properties(self, button):
        properties_window = Properties(self, self.game, self.config, self.api)
        properties_window.run()
        properties_window.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def on_button_cancel(self, widget):
        question = _("Are you sure you want to cancel downloading {}?").format(self.game.name)
        if self.parent.parent.show_question(question):
            self.prevent_resume_on_startup()
            self.download_manager.cancel_download(self.download_list)
            try:
                for filename in os.listdir(self.download_dir):
                    if self.game.get_install_directory_name() in filename:
                        os.remove(os.path.join(self.download_dir, filename))
            except FileNotFoundError:
                pass

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        question = _("Are you sure you want to uninstall %s?" % self.game.name)
        if self.parent.parent.show_question(question):
            uninstall_thread = threading.Thread(target=self.__uninstall_game)
            uninstall_thread.start()

    @Gtk.Template.Callback("on_menu_button_update_clicked")
    def on_menu_button_update(self, widget):
        download_thread = threading.Thread(target=self.__download_update)
        download_thread.start()

    def load_thumbnail(self):
        set_result = self.__set_image("")
        if not set_result:
            tries = 10
            performed_try = 0
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
            current_download_ids = self.config.current_downloads
            if current_download_ids:
                new_current_download_ids = set()
                for current_download_id in current_download_ids:
                    if current_download_id != self.game.id:
                        new_current_download_ids.add(current_download_id)
                self.config.current_downloads = list(new_current_download_ids)
            GLib.idle_add(self.parent.parent.show_error, _("Download error"),
                          _("There was an error when trying to fetch the download link!\n{}".format(e)))
            download_info = False
            result = False
        return result, download_info

    def __download_game(self) -> None:
        finish_func = self.__install_game
        cancel_to_state = State.DOWNLOADABLE
        result, download_info = self.get_download_info()
        if result:
            result = self.__download(download_info, DownloadType.GAME, finish_func,
                                     cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __download(self, download_info, download_type, finish_func, cancel_to_state):  # noqa: C901
        download_success = True
        self.game.set_install_dir(self.config.install_dir)
        GLib.idle_add(self.update_to_state, State.QUEUED)

        # Need to update the config with DownloadType metadata
        current_download_ids = self.config.current_downloads
        if current_download_ids is None:
            current_download_ids = set()
        else:
            current_download_ids = set(current_download_ids)
        current_download_ids.add(self.game.id)
        self.config.current_downloads = list(current_download_ids)
        # Start the download for all files
        self.download_list = []
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
                GLib.idle_add(self.parent.parent.show_error, _("Download error"), _(str(e)))
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
                download_type=DownloadType.GAME,
                finish_func=finish_func_wrapper(finish_func),
                progress_func=self.set_progress,
                cancel_func=lambda: self.__cancel(to_state=cancel_to_state),
                number=number_of_files - key,
                out_of_amount=number_of_files,
                game=self.game
            )
            download_files.insert(0, download)
        self.download_list.extend(download_files)

        if check_diskspace(total_file_size, self.game.install_dir):
            self.download_manager.download(download_files)
            ds_msg_title = ""
            ds_msg_text = ""
        else:
            ds_msg_title = "Download error"
            ds_msg_text = "Not enough disk space to install game."
            download_success = False
        if ds_msg_title:
            GLib.idle_add(self.parent.parent.show_error, _(ds_msg_title), _(ds_msg_text))
        return download_success

    def __install_game(self, save_location):
        if self.game.id in self.config.current_downloads:
            self.config.current_downloads.remove(self.game.id)
        self.download_list = []
        self.game.set_install_dir(self.config.install_dir)
        install_success = self.__install(save_location)
        if install_success:
            self.__check_for_dlc(self.api.get_info(self.game))

    def __install(self, save_location, update=False, dlc_title=""):
        if update:
            processing_state = State.UPDATING
            failed_state = State.INSTALLED
        else:
            processing_state = State.INSTALLING
            failed_state = State.DOWNLOADABLE
        success_state = State.INSTALLED
        GLib.idle_add(self.update_to_state, processing_state)
        err_msg = install_game(
            self.game,
            save_location,
            self.config
        )
        if not err_msg:
            GLib.idle_add(self.update_to_state, success_state)
            install_success = True
            if dlc_title:
                self.game.set_dlc_info("version", self.api.get_version(self.game, dlc_name=dlc_title), dlc_title)
            else:
                self.game.set_info("version", self.api.get_version(self.game))
            popup = Notify.Notification.new("Minigalaxy", _("Finished downloading and installing {}")
                                            .format(self.game.name), "dialog-information")
            popup.show()
        else:
            GLib.idle_add(self.parent.parent.show_error, _("Failed to install {}").format(self.game.name), err_msg)
            GLib.idle_add(self.update_to_state, failed_state)
            install_success = False
        return install_success

    def __cancel(self, to_state):
        self.download_list = []
        GLib.idle_add(self.update_to_state, to_state)
        GLib.idle_add(self.reload_state)

    def __download_update(self) -> None:
        finish_func = self.__update
        cancel_to_state = State.UPDATABLE
        result, download_info = self.get_download_info(self.game.platform)
        if result:
            result = self.__download(download_info, DownloadType.GAME_UPDATE, finish_func,
                                     cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __check_for_update_dlc(self):
        if self.game.is_installed() and self.game.id and not self.offline:
            game_info = self.api.get_info(self.game)
            if self.game.get_info("check_for_updates") == "":
                self.game.set_info("check_for_updates", True)
            if self.game.get_info("check_for_updates"):
                game_version = self.api.get_version(self.game, gameinfo=game_info)
                update_available = self.game.is_update_available(game_version)
                if update_available:
                    GLib.idle_add(self.update_to_state, State.UPDATABLE)
            self.__check_for_dlc(game_info)
        if self.offline:
            GLib.idle_add(self.menu_button_dlc.hide)

    def __update(self, save_location):
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

    def __download_dlc(self, dlc_installers) -> None:
        def finish_func(save_location):
            self.__install_dlc(save_location, dlc_title=dlc_title)

        download_info = self.api.get_download_info(self.game, dlc_installers=dlc_installers)
        dlc_title = self.game.name
        for dlc in self.game.dlcs:
            if dlc["downloads"]["installers"] == dlc_installers:
                dlc_title = dlc["title"]
        cancel_to_state = State.INSTALLED
        result = self.__download(download_info, DownloadType.GAME_DLC, finish_func,
                                 cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __install_dlc(self, save_location, dlc_title):
        install_success = self.__install(save_location, dlc_title=dlc_title)
        if not install_success:
            GLib.idle_add(self.update_to_state, State.INSTALLED)
        self.__check_for_update_dlc()

    def __check_for_dlc(self, game_info):
        dlcs = game_info["expanded_dlcs"]
        for dlc in dlcs:
            if dlc["is_installable"] and dlc["id"] in self.parent.owned_products_ids:
                d_id = dlc["id"]
                d_installer = dlc["downloads"]["installers"]
                d_icon = dlc["images"]["sidebarIcon"]
                d_name = dlc["title"]
                GLib.idle_add(self.update_gtk_box_for_dlc, d_id, d_icon, d_name, d_installer)
                if dlc not in self.game.dlcs:
                    self.game.dlcs.append(dlc)
        if self.game.dlcs:
            GLib.idle_add(self.menu_button_dlc.show)

    def update_gtk_box_for_dlc(self, dlc_id, icon, title, installer):
        if title not in self.dlc_dict:
            dlc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            dlc_box.set_spacing(8)
            image = Gtk.Image()
            image.set_from_icon_name("media-optical", Gtk.IconSize.BUTTON)
            dlc_box.pack_start(image, False, True, 0)
            label = Gtk.Label(label=title, xalign=0)
            dlc_box.pack_start(label, True, True, 0)
            install_button = Gtk.Button()
            dlc_box.pack_start(install_button, False, True, 0)
            self.dlc_dict[title] = [install_button, image]
            self.dlc_dict[title][0].connect("clicked", self.__dlc_button_clicked, installer)
            self.dlc_horizontal_box.pack_start(dlc_box, False, True, 0)
            dlc_box.show_all()
            self.get_async_image_dlc_icon(dlc_id, image, icon, title)
        download_info = self.api.get_download_info(self.game, dlc_installers=installer)
        if self.game.is_update_available(version_from_api=download_info["version"], dlc_title=title):
            icon_name = "emblem-synchronizing"
            self.dlc_dict[title][0].set_sensitive(True)
        elif self.game.is_installed(dlc_title=title):
            icon_name = "object-select"
            self.dlc_dict[title][0].set_sensitive(False)
        else:
            icon_name = "document-save"
            if not self.download_list:
                self.dlc_dict[title][0].set_sensitive(True)
        install_button_image = Gtk.Image()
        install_button_image.set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        self.dlc_dict[title][0].set_image(install_button_image)

    def __dlc_button_clicked(self, button, installer):
        button.set_sensitive(False)
        threading.Thread(target=self.__download_dlc, args=(installer,)).start()

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

    def __uninstall_game(self):
        GLib.idle_add(self.update_to_state, State.UNINSTALLING)
        uninstall_game(self.game)
        GLib.idle_add(self.update_to_state, State.DOWNLOADABLE)
        GLib.idle_add(self.reload_state)

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

    def __state_downloadable(self):
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

    def __state_installable(self):
        self.button.set_label(_("Install"))
        self.button.set_tooltip_text(_("Install the game"))
        self.button.set_sensitive(True)
        self.image.set_sensitive(False)
        self.menu_button.hide()
        self.button_cancel.hide()
        self.progress_bar.hide()

        self.game.install_dir = ""

    def __state_queued(self):
        self.button.set_label(_("In queue…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.show()
        self.progress_bar.show()

    def __state_downloading(self):
        self.button.set_label(_("Downloading…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.show()
        self.progress_bar.show()

    def __state_installing(self):
        self.button.set_label(_("Installing…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(True)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.hide()
        self.progress_bar.hide()

        self.game.set_install_dir(self.config.install_dir)
        self.parent.filter_library()

    def __state_installed(self):
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

    def __state_uninstalling(self):
        self.button.set_label(_("Uninstalling…"))
        self.button.get_style_context().remove_class("suggested-action")
        self.menu_button.get_style_context().remove_class("suggested-action")
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button.hide()
        self.button_cancel.hide()

        self.game.install_dir = ""
        self.parent.filter_library()

    def __state_updatable(self):
        self.update_icon.show()
        self.update_icon.set_from_icon_name("emblem-synchronizing", Gtk.IconSize.LARGE_TOOLBAR)
        self.button.set_label(_("Play"))
        self.menu_button.show()
        tooltip_text = "{} (update{})".format(self.game.name, ", Wine" if self.game.platform == "windows" else "")
        self.image.set_tooltip_text(tooltip_text)
        self.menu_button_update.show()
        if self.game.platform == "windows":
            self.wine_icon.set_margin_left(22)

    def __state_updating(self):
        self.button.set_label(_("Updating…"))

    STATE_UPDATE_HANDLERS = {
        State.DOWNLOADABLE: __state_downloadable,
        State.INSTALLABLE: __state_installable,
        State.QUEUED: __state_queued,
        State.DOWNLOADING: __state_downloading,
        State.INSTALLING: __state_installing,
        State.INSTALLED: __state_installed,
        State.UNINSTALLING: __state_uninstalling,
        State.UPDATABLE: __state_updatable,
        State.UPDATING: __state_updating,
    }

    def update_to_state(self, state):
        self.current_state = state
        if state in self.STATE_UPDATE_HANDLERS:
            self.STATE_UPDATE_HANDLERS[state](self)
