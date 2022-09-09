import shutil
import locale
import os
import threading
import re
import time
import urllib.parse
from enum import Enum
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, ICON_DIR, UI_DIR
from minigalaxy.config import Config
from minigalaxy.download import Download
from minigalaxy.download_manager import DownloadManager
from minigalaxy.launcher import start_game
from minigalaxy.installer import uninstall_game, install_game, check_diskspace
from minigalaxy.css import CSS_PROVIDER
from minigalaxy.paths import ICON_WINE_PATH
from minigalaxy.api import NoDownloadLinkFound
from minigalaxy.ui.gtk import Gtk, GLib
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

    state = Enum('state',
                 'DOWNLOADABLE INSTALLABLE UPDATABLE QUEUED DOWNLOADING INSTALLING INSTALLED NOTLAUNCHABLE UNINSTALLING'
                 ' UPDATING UPDATE_INSTALLABLE')

    def __init__(self, parent, game):
        current_locale = Config.get("locale")
        default_locale = locale.getdefaultlocale()[0]
        if current_locale == '':
            locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        else:
            try:
                locale.setlocale(locale.LC_ALL, (current_locale, 'UTF-8'))
            except NameError:
                locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        Gtk.Frame.__init__(self)
        Gtk.StyleContext.add_provider(self.button.get_style_context(),
                                      CSS_PROVIDER,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.parent = parent
        self.game = game
        self.api = parent.api
        self.offline = parent.offline
        self.progress_bar = None
        self.thumbnail_set = False
        self.download_list = []
        self.dlc_dict = {}
        self.current_state = self.state.DOWNLOADABLE

        self.image.set_tooltip_text(self.game.name)

        # Set folder for download installer
        self.download_dir = os.path.join(CACHE_DIR, "download", self.game.get_install_directory_name())

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(Config.get("install_dir"), "installer")
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
        download_id = Config.get("current_download")
        if download_id and download_id == self.game.id and self.current_state == self.state.DOWNLOADABLE:
            download_thread = threading.Thread(target=self.__download_game)
            download_thread.start()

    # Do not restart the download if Minigalaxy is restarted
    def prevent_resume_on_startup(self):
        download_id = Config.get("current_download")
        if download_id and download_id == self.game.id:
            Config.unset("current_download")

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        dont_act_in_states = [self.state.QUEUED, self.state.DOWNLOADING, self.state.INSTALLING, self.state.UNINSTALLING]
        err_msg = ""
        if self.current_state in dont_act_in_states:
            pass
        elif self.current_state in [self.state.INSTALLED, self.state.UPDATABLE]:
            err_msg = start_game(self.game)
        elif self.current_state == self.state.INSTALLABLE:
            install_thread = threading.Thread(target=self.__install_game, args=(self.get_keep_executable_path(),))
            install_thread.start()
        elif self.current_state == self.state.DOWNLOADABLE:
            download_thread = threading.Thread(target=self.__download_game)
            download_thread.start()
        if err_msg:
            self.parent.parent.show_error(_("Failed to start {}:").format(self.game.name), err_msg)

    @Gtk.Template.Callback("on_menu_button_information_clicked")
    def show_information(self, button):
        information_window = Information(self, self.game, self.api)
        information_window.run()
        information_window.destroy()

    @Gtk.Template.Callback("on_menu_button_properties_clicked")
    def show_properties(self, button):
        properties_window = Properties(self, self.game, self.api)
        properties_window.run()
        properties_window.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def on_button_cancel(self, widget):
        question = _("Are you sure you want to cancel downloading {}?").format(self.game.name)
        if self.parent.parent.show_question(question):
            self.prevent_resume_on_startup()
            DownloadManager.cancel_download(self.download_list)
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

                    download = Download(image_url, thumbnail, finish_func=self.__set_image)
                    DownloadManager.download_now(download)
                    set_result = True
                    break
                performed_try += 1
                time.sleep(1)
        return set_result

    def __set_image(self, save_location):
        set_result = False
        self.game.set_install_dir()
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
            print(e)
            if Config.get("current_download") == self.game.id:
                Config.unset("current_download")
            GLib.idle_add(self.parent.parent.show_error, _("Download error"),
                          _("There was an error when trying to fetch the download link!\n{}".format(e)))
            download_info = False
            result = False
        return result, download_info

    def __download_game(self) -> None:
        finish_func = self.__install_game
        cancel_to_state = self.state.DOWNLOADABLE
        result, download_info = self.get_download_info()
        if result:
            result = self.__download(download_info, finish_func, cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __download(self, download_info, finish_func, cancel_to_state):
        download_success = True
        GLib.idle_add(self.update_to_state, self.state.QUEUED)
        Config.set("current_download", self.game.id)
        # Start the download for all files
        self.download_list = []
        number_of_files = len(download_info['files'])
        total_file_size = 0
        executable_path = None
        download_files = []
        for key, file_info in enumerate(download_info['files']):
            try:
                download_url = self.api.get_real_download_link(file_info["downlink"])
            except ValueError as e:
                print(e)
                GLib.idle_add(self.parent.parent.show_error, _("Download error"), _(str(e)))
                download_success = False
                break
            info = self.api.get_download_file_info(file_info["downlink"])
            total_file_size += info.size
            try:
                # Extract the filename from the download url (filename is between %2F and &token)
                filename = urllib.parse.unquote(re.search('%2F(((?!%2F).)*)&t', download_url).group(1))
            except AttributeError:
                filename = "{}-{}.bin".format(self.game.get_stripped_name(), key)
            download_path = os.path.join(self.download_dir, filename)
            if key == 0:
                # If key = 0, denote the file as the executable's path
                executable_path = download_path
            if info.md5:
                self.game.md5sum[os.path.basename(download_path)] = info.md5
            download = Download(
                url=download_url,
                save_location=download_path,
                finish_func=finish_func if download_path == executable_path else None,
                progress_func=self.set_progress,
                cancel_func=lambda: self.__cancel(to_state=cancel_to_state),
                number=number_of_files - key,
                out_of_amount=number_of_files,
                game=self.game
            )
            download_files.insert(0, download)
        self.download_list.extend(download_files)

        if check_diskspace(total_file_size, Config.get("install_dir")):
            DownloadManager.download(download_files)
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
        self.download_list = []
        self.game.set_install_dir()
        install_success = self.__install(save_location)
        if install_success:
            self.__check_for_dlc(self.api.get_info(self.game))

    def __install(self, save_location, update=False, dlc_title=""):
        if update:
            processing_state = self.state.UPDATING
            failed_state = self.state.INSTALLED
        else:
            processing_state = self.state.INSTALLING
            failed_state = self.state.DOWNLOADABLE
        success_state = self.state.INSTALLED
        GLib.idle_add(self.update_to_state, processing_state)
        err_msg = install_game(self.game, save_location)
        if not err_msg:
            GLib.idle_add(self.update_to_state, success_state)
            install_success = True
            if dlc_title:
                self.game.set_dlc_info("version", self.api.get_version(self.game, dlc_name=dlc_title), dlc_title)
            else:
                self.game.set_info("version", self.api.get_version(self.game))
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
        cancel_to_state = self.state.UPDATABLE
        result, download_info = self.get_download_info(self.game.platform)
        if result:
            result = self.__download(download_info, finish_func, cancel_to_state)
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
                    GLib.idle_add(self.update_to_state, self.state.UPDATABLE)
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
        cancel_to_state = self.state.INSTALLED
        result = self.__download(download_info, finish_func, cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __install_dlc(self, save_location, dlc_title):
        install_success = self.__install(save_location, dlc_title=dlc_title)
        if not install_success:
            GLib.idle_add(self.update_to_state, self.state.INSTALLED)
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
                DownloadManager.download_now(download)
                GLib.idle_add(image.set_from_file, dlc_icon_path)

    def set_progress(self, percentage: int):
        if self.current_state in [self.state.QUEUED, self.state.INSTALLED]:
            GLib.idle_add(self.update_to_state, self.state.DOWNLOADING)
            self.__create_progress_bar()
        if self.progress_bar:
            GLib.idle_add(self.progress_bar.set_fraction, percentage / 100)
            GLib.idle_add(self.progress_bar.set_tooltip_text, "{}%".format(percentage))

    def __uninstall_game(self):
        GLib.idle_add(self.update_to_state, self.state.UNINSTALLING)
        uninstall_game(self.game)
        GLib.idle_add(self.update_to_state, self.state.DOWNLOADABLE)
        GLib.idle_add(self.reload_state)

    def __create_progress_bar(self) -> None:
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_halign(Gtk.Align.CENTER)
        self.progress_bar.set_size_request(196, -1)
        self.progress_bar.set_hexpand(False)
        self.progress_bar.set_vexpand(False)
        self.set_center_widget(self.progress_bar)
        self.progress_bar.set_fraction(0.0)

    def reload_state(self):
        self.game.set_install_dir()
        dont_act_in_states = [self.state.QUEUED, self.state.DOWNLOADING, self.state.INSTALLING, self.state.UNINSTALLING,
                              self.state.UPDATING, self.state.DOWNLOADING]
        if self.current_state in dont_act_in_states:
            return
        if self.game.is_installed():
            self.update_to_state(self.state.INSTALLED)
            check_update_thread = threading.Thread(target=self.__check_for_update_dlc)
            check_update_thread.start()
        elif self.get_keep_executable_path():
            self.update_to_state(self.state.INSTALLABLE)
        else:
            self.update_to_state(self.state.DOWNLOADABLE)

    def __state_downloadable(self):
        self.button.set_label(_("download"))
        self.button.set_sensitive(True)
        self.image.set_sensitive(False)

        # The user must have the possibilty to access
        # to the store button even if the game is not installed
        self.menu_button.show()
        self.menu_button_update.hide()
        self.menu_button_dlc.hide()
        self.menu_button_uninstall.hide()

        self.button_cancel.hide()

        self.game.install_dir = ""

        if self.progress_bar:
            self.progress_bar.destroy()

    def __state_installable(self):
        self.button.set_label(_("install"))
        self.button.set_sensitive(True)
        self.image.set_sensitive(False)
        self.menu_button.hide()
        self.button_cancel.hide()

        self.game.install_dir = ""

        if self.progress_bar:
            self.progress_bar.destroy()

    def __state_queued(self):
        self.button.set_label(_("in queue…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.show()
        self.__create_progress_bar()

    def __state_downloading(self):
        self.button.set_label(_("downloading…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.show()
        if not self.progress_bar:
            self.__create_progress_bar()
        self.progress_bar.show_all()

    def __state_installing(self):
        self.button.set_label(_("installing…"))
        self.button.set_sensitive(False)
        self.image.set_sensitive(True)
        self.menu_button_uninstall.hide()
        self.menu_button_update.hide()
        self.button_cancel.hide()

        self.game.set_install_dir()

        if self.progress_bar:
            self.progress_bar.destroy()

        self.parent.filter_library()

    def __state_installed(self):
        self.button.set_label(_("play"))
        self.button.get_style_context().add_class("suggested-action")
        self.button.set_sensitive(True)
        self.image.set_sensitive(True)
        self.menu_button.show()
        self.menu_button_uninstall.show()
        self.button_cancel.hide()
        self.game.set_install_dir()

        if self.progress_bar:
            self.progress_bar.destroy()

        self.menu_button_update.hide()
        self.update_icon.hide()

    def __state_uninstalling(self):
        self.button.set_label(_("uninstalling…"))
        self.button.get_style_context().remove_class("suggested-action")
        self.button.set_sensitive(False)
        self.image.set_sensitive(False)
        self.menu_button.hide()
        self.button_cancel.hide()

        self.game.install_dir = ""

        self.parent.filter_library()

    def __state_updatable(self):
        self.update_icon.show()
        self.update_icon.set_from_icon_name("emblem-synchronizing", Gtk.IconSize.LARGE_TOOLBAR)
        self.button.set_label(_("play"))
        self.menu_button.show()
        tooltip_text = "{} (update{})".format(self.game.name, ", Wine" if self.game.platform == "windows" else "")
        self.image.set_tooltip_text(tooltip_text)
        self.menu_button_update.show()
        if self.game.platform == "windows":
            self.wine_icon.set_margin_left(22)

    def __state_updating(self):
        self.button.set_label(_("updating…"))

    STATE_UPDATE_HANDLERS = {
        state.DOWNLOADABLE: __state_downloadable,
        state.INSTALLABLE: __state_installable,
        state.QUEUED: __state_queued,
        state.DOWNLOADING: __state_downloading,
        state.INSTALLING: __state_installing,
        state.INSTALLED: __state_installed,
        state.UNINSTALLING: __state_uninstalling,
        state.UPDATABLE: __state_updatable,
        state.UPDATING: __state_updating,
    }

    def update_to_state(self, state):
        self.current_state = state
        if state in self.STATE_UPDATE_HANDLERS:
            self.STATE_UPDATE_HANDLERS[state](self)
