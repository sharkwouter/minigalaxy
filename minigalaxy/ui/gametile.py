import shutil
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf, Gio
import os
import webbrowser
import threading
import subprocess
import re
import urllib.parse
from gi.repository.GdkPixbuf import Pixbuf
from enum import Enum
from zipfile import BadZipFile
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, UI_DIR
from minigalaxy.config import Config
from minigalaxy.download import Download
from minigalaxy.download_manager import DownloadManager
from minigalaxy.launcher import start_game, config_game
from minigalaxy.installer import uninstall_game, install_game
from minigalaxy.css import CSS_PROVIDER
from minigalaxy.paths import ICON_WINE_PATH
from minigalaxy.paths import ICON_UPDATE_PATH
from minigalaxy.api import NoDownloadLinkFound


@Gtk.Template.from_file(os.path.join(UI_DIR, "gametile.ui"))
class GameTile(Gtk.Box):
    __gtype_name__ = "GameTile"
    gogBaseUrl = "https://www.gog.com"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    menu_button_settings = Gtk.Template.Child()
    wine_icon = Gtk.Template.Child()
    update_icon = Gtk.Template.Child()
    menu_button_store = Gtk.Template.Child()
    menu_button_update = Gtk.Template.Child()
    menu_button_dlc = Gtk.Template.Child()
    dlc_horizontal_box = Gtk.Template.Child()

    state = Enum('state',
                 'DOWNLOADABLE INSTALLABLE UPDATABLE QUEUED DOWNLOADING INSTALLING INSTALLED NOTLAUNCHABLE UNINSTALLING'
                 ' UPDATING UPDATE_INSTALLABLE')

    def __init__(self, parent, game, api, offline):
        Gtk.Frame.__init__(self)
        Gtk.StyleContext.add_provider(self.button.get_style_context(),
                                      CSS_PROVIDER,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.parent = parent
        self.game = game
        self.api = api
        self.offline = offline
        self.progress_bar = None
        self.thumbnail_set = False
        self.download = None
        self.dlc_dict = {}
        self.current_state = self.state.DOWNLOADABLE

        self.image.set_tooltip_text(self.game.name)

        # Set folder for download installer
        self.download_dir = os.path.join(CACHE_DIR, "download", self.game.get_install_directory_name())
        self.download_path = os.path.join(self.download_dir, self.game.get_install_directory_name())

        # Set folder for update installer
        self.update_dir = os.path.join(CACHE_DIR, "update")
        self.update_path = os.path.join(self.update_dir, self.game.name)

        # Set folder for dlc installer
        self.dlc_dir = os.path.join(CACHE_DIR, "dlc")

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(Config.get("install_dir"), "installer")
        self.keep_path = os.path.join(self.keep_dir, self.game.get_install_directory_name())
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, mode=0o755)

        self.reload_state()
        self.load_thumbnail()

        # Start download if Minigalaxy was closed while downloading this game
        self.resume_download_if_expected()

        # Icon for Windows games
        if self.game.platform == "windows":
            self.image.set_tooltip_text("{} (Wine)".format(self.game.name))
            self.wine_icon.set_from_file(ICON_WINE_PATH)
            self.wine_icon.show()

        if not self.game.url:
            self.menu_button_store.hide()

    # Downloads if Minigalaxy was closed with this game downloading
    def resume_download_if_expected(self):
        download_id = Config.get("current_download")
        if download_id and download_id == self.game.id and self.current_state == self.state.DOWNLOADABLE:
            download_thread = threading.Thread(target=self.__download_file)
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
        if self.current_state in dont_act_in_states:
            return
        elif self.current_state in [self.state.INSTALLED, self.state.UPDATABLE]:
            start_game(self.game, self.parent)
        elif self.current_state == self.state.INSTALLABLE:
            install_thread = threading.Thread(target=self.__install)
            install_thread.start()
        elif self.current_state == self.state.DOWNLOADABLE:
            download_thread = threading.Thread(target=self.__download_file)
            download_thread.start()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def on_button_cancel(self, widget):
        question = _("Are you sure you want to cancel downloading {}?").format(self.game.name)
        if self.parent.parent.show_question(question):
            self.prevent_resume_on_startup()
            DownloadManager.cancel_download(self.download)
            for filename in os.listdir(self.download_dir):
                if self.game.get_install_directory_name() in filename:
                    os.remove(os.path.join(self.download_dir, filename))

    @Gtk.Template.Callback("on_menu_button_settings_clicked")
    def on_menu_button_settings(self, widget):
        config_game(self.game)

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        question = _("Are you sure you want to uninstall %s?" % self.game.name)
        if self.parent.parent.show_question(question):
            uninstall_thread = threading.Thread(target=self.__uninstall_game)
            uninstall_thread.start()

    @Gtk.Template.Callback("on_menu_button_open_clicked")
    def on_menu_button_open_files(self, widget):
        subprocess.call(["xdg-open", self.__get_install_dir()])

    @Gtk.Template.Callback("on_menu_button_support_clicked")
    def on_menu_button_support(self, widget):
        try:
            webbrowser.open(self.api.get_info(self.game)['links']['support'], new=2)
        except:
            self.parent.parent.show_error(
                _("Couldn't open support page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_menu_button_store_clicked")
    def on_menu_button_store(self, widget):
        webbrowser.open(self.gogBaseUrl + self.game.url)

    @Gtk.Template.Callback("on_menu_button_update_clicked")
    def on_menu_button_update(self, widget):
        download_thread = threading.Thread(target=self.__download_update)
        download_thread.start()

    def load_thumbnail(self):
        if self.__set_image():
            return True
        if not self.game.image_url or not self.game.id:
            return False

        # Download the thumbnail
        image_url = "https:{}_196.jpg".format(self.game.image_url)
        thumbnail = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))

        download = Download(image_url, thumbnail, finish_func=self.__set_image)
        DownloadManager.download_now(download)
        return True

    def __set_image(self):
        thumbnail_install_dir = os.path.join(self.__get_install_dir(), "thumbnail.jpg")
        thumbnail_cache_dir = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
        if os.path.isfile(thumbnail_install_dir):
            GLib.idle_add(self.image.set_from_file, thumbnail_install_dir)
            return True
        elif os.path.isfile(thumbnail_cache_dir):
            GLib.idle_add(self.image.set_from_file, thumbnail_cache_dir)
            # Copy image to
            if os.path.isdir(os.path.dirname(thumbnail_install_dir)):
                shutil.copy2(thumbnail_cache_dir, thumbnail_install_dir)
            return True
        return False

    def get_keep_executable_path(self):
        if os.path.exists(self.keep_path):
            if os.path.isdir(self.keep_path):
                for fil in os.scandir(self.keep_path):
                    if os.access(fil.path, os.X_OK) or os.path.splitext(fil)[-1] == ".exe" or os.path.splitext(fil)[-1] == ".sh":
                        return fil.path
            elif os.path.isfile(self.keep_path):
                # This is only the case for installers that have been downloaded with versions <= 0.9.4
                return self.keep_path
        return ""

    def __download_file(self) -> None:
        GLib.idle_add(self.update_to_state, self.state.QUEUED)
        try:
            download_info = self.api.get_download_info(self.game)
        except NoDownloadLinkFound:
            if Config.get("current_download") == self.game.id:
                Config.unset("current_download")
            GLib.idle_add(self.parent.parent.show_error, _("Download error"), _("There was an error when trying to fetch the download link!"))
            GLib.idle_add(self.update_to_state, self.state.DOWNLOADABLE)
            return
        
        Config.set("current_download", self.game.id)
        # Start the download for all files
        self.download = []
        download_path = self.download_path
        finish_func = self.__install
        number_of_files = len(download_info['files'])
        for key, file_info in enumerate(download_info['files']):
            download_url = self.api.get_real_download_link(file_info["downlink"])
            try:
                # Extract the filename from the download url (filename is between %2F and &token)
                download_path = os.path.join(self.download_dir, urllib.parse.unquote(re.search('%2F(((?!%2F).)*)&t', download_url).group(1)))
                if key == 0:
                    # If key = 0, denote the file as the executable's path
                    self.download_path = download_path
            except AttributeError:
                if key > 0:
                    download_path = "{}-{}.bin".format(self.download_path, key)
            download = Download(
                url=download_url,
                save_location=download_path,
                finish_func=finish_func,
                progress_func=self.set_progress,
                cancel_func=self.__cancel_download,
                number=key+1,
                out_of_amount=number_of_files
            )
            self.download.append(download)

        DownloadManager.download(self.download)

    def __install(self):
        GLib.idle_add(self.update_to_state, self.state.INSTALLING)
        self.game.install_dir = self.__get_install_dir()
        try:
            keep_executable_path = self.get_keep_executable_path()
            if keep_executable_path:
                install_game(self.game, keep_executable_path, main_window=self.parent.parent)
            else:
                install_game(self.game, self.download_path, main_window=self.parent.parent)
        except (FileNotFoundError, BadZipFile):
            GLib.idle_add(self.update_to_state, self.state.DOWNLOADABLE)
            return
        GLib.idle_add(self.update_to_state, self.state.INSTALLED)

    def __cancel_download(self):
        GLib.idle_add(self.update_to_state, self.state.DOWNLOADABLE)
        GLib.idle_add(self.reload_state)

    def __download_update(self) -> None:
        Config.set("current_download", self.game.id)
        GLib.idle_add(self.update_to_state, self.state.QUEUED)
        download_info = self.api.get_download_info(self.game)

        # Start the download for all files
        self.download = []
        download_path = self.update_path
        for key, file_info in enumerate(download_info['files']):
            if key > 0:
                download_path = "{}-{}.bin".format(self.update_path, key)
            download = Download(
                url=self.api.get_real_download_link(file_info["downlink"]),
                save_location=download_path,
                finish_func=self.__update,
                progress_func=self.set_progress,
                cancel_func=self.__cancel_update,
                number=key+1,
                out_of_amount=len(download_info['files'])
            )
            self.download.append(download)

        DownloadManager.download(self.download)

    def __check_for_update_dlc(self):
        if self.game.installed_version and self.game.id and not self.offline:
            game_info = self.api.get_info(self.game)
            installer = game_info["downloads"]["installers"]
            update_available = self.game.validate_if_installed_is_latest(installer)
            if update_available:
                self.update_to_state(self.state.UPDATABLE)
            self.__check_for_dlc(game_info)

    def __update(self):
        GLib.idle_add(self.update_to_state, self.state.UPDATING)
        self.game.install_dir = self.__get_install_dir()
        try:
            install_game(self.game, self.update_path, main_window=self.parent.parent)
            install_success = True
        except (FileNotFoundError, BadZipFile) as e:
            print("Warning: {}".format(e))
            GLib.idle_add(self.update_to_state, self.state.UPDATABLE)
            install_success = False
        if install_success:
            GLib.idle_add(self.update_to_state, self.state.INSTALLED)
            if self.game.platform == "windows":
                self.image.set_tooltip_text("{} (Wine)".format(self.game.name))
            else:
                self.image.set_tooltip_text(self.game.name)

    def __cancel_update(self):
        GLib.idle_add(self.update_to_state, self.state.UPDATABLE)
        GLib.idle_add(self.reload_state)

    def __download_dlc(self, dlc_installers) -> None:
        Config.set("current_download", self.game.id)
        GLib.idle_add(self.update_to_state, self.state.QUEUED)
        download_info = self.api.get_download_info(self.game, dlc=True, dlc_installers=dlc_installers)

        # Start the download for all files
        dlc_path = os.path.join(self.dlc_dir, self.game.name)
        dlc_title = self.game.name
        for dlc in self.game.dlcs:
            if dlc["downloads"]["installers"] == dlc_installers:
                dlc_title = dlc["title"]
                dlc_path = os.path.join(self.dlc_dir, dlc_title)
        self.download = []
        key = 1
        for dlc_file in download_info['files']:
            print(dlc_file)
            download_path = "{}-{}.bin".format(dlc_path, dlc_file["id"])
            download = Download(
                url=self.api.get_real_download_link(dlc_file["downlink"]),
                save_location=download_path,
                finish_func=lambda: self.__install_dlc(dlc_title, download_path),
                progress_func=self.set_progress,
                cancel_func=self.__cancel_dlc,
                number=key,
                out_of_amount=len(download_info['files'])
            )
            self.download.append(download)
            key += 1

        DownloadManager.download(self.download)

    def __install_dlc(self, dlc_title, dlc_download_path):
        print("download dlc ready")
        GLib.idle_add(self.update_to_state, self.state.INSTALLING)
        self.game.install_dir = self.__get_install_dir()
        try:
            install_game(self.game, dlc_download_path, main_window=self.parent.parent)
            install_success = True
        except (FileNotFoundError, BadZipFile) as e:
            print("Warning: {}".format(e))
            install_success = False
        GLib.idle_add(self.update_to_state, self.state.INSTALLED)
        self.game.set_dlc_status(dlc_title, install_success)
        self.__check_for_dlc(self.api.get_info(self.game))

    def __cancel_dlc(self):
        GLib.idle_add(self.update_to_state, self.state.INSTALLED)
        GLib.idle_add(self.reload_state)

    def __check_for_dlc(self, game_info):
        dlcs = game_info["expanded_dlcs"]
        if dlcs:
            self.menu_button_dlc.show()
        else:
            self.menu_button_dlc.hide()
        for dlc in dlcs:
            d_installer = dlc["downloads"]["installers"]
            if d_installer:
                d_icon = dlc["images"]["sidebarIcon"]
                d_name = dlc["title"]
                d_status = self.game.get_dlc_status(d_name)
                self.dlc_box(d_icon, d_name, d_status, d_installer)
                if dlc not in self.game.dlcs:
                    self.game.dlcs.append(dlc)

    def dlc_box(self, icon, title, status, installer):
        if title not in self.dlc_dict:
            dlc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            image = Gtk.Image()
            image.set_from_icon_name("gtk-cdrom", 1)
            dlc_box.pack_start(image, False, True, 0)
            label = Gtk.Label(label=title, xalign=0)
            dlc_box.pack_start(label, True, True, 0)
            install_button = Gtk.Button()
            dlc_box.pack_start(install_button, False, True, 0)
            self.dlc_dict[title] = [install_button, image]
            self.dlc_dict[title][0].connect("clicked", lambda x: self.__download_dlc(installer))
            self.dlc_horizontal_box.pack_start(dlc_box, False, True, 0)
            dlc_box.show_all()
            self.get_async_image_dlc_icon(icon, title)
        if status.lower() == "installed":
            icon_name = "gtk-ok"
            self.dlc_dict[title][0].set_sensitive(False)
        else:
            icon_name = "gtk-goto-bottom"
            self.dlc_dict[title][0].set_sensitive(True)
        install_button_image = Gtk.Image()
        install_button_image.set_from_icon_name(icon_name, 1)
        self.dlc_dict[title][0].set_image(install_button_image)

    def get_async_image_dlc_icon(self, icon, title):
        if icon:
            url = "http:{}".format(icon)
            response = Gio.File.new_for_uri(url)
            response.read_async(3, None, self.set_proper_dlc_icon, title)

    def set_proper_dlc_icon(self, source, async_res, user_data):
        response = source.read_finish(async_res)
        pixbuf = Pixbuf.new_from_stream(response)
        self.dlc_dict[user_data][1].set_from_pixbuf(pixbuf)

    def set_progress(self, percentage: int):
        if self.current_state == self.state.QUEUED:
            GLib.idle_add(self.update_to_state, self.state.DOWNLOADING)
        if self.progress_bar:
            GLib.idle_add(self.progress_bar.set_fraction, percentage/100)

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

    def __get_install_dir(self):
        if self.game.install_dir:
            return self.game.install_dir
        return os.path.join(Config.get("install_dir"), self.game.get_install_directory_name())

    def reload_state(self):
        self.game.install_dir = self.__get_install_dir()
        dont_act_in_states = [self.state.QUEUED, self.state.DOWNLOADING, self.state.INSTALLING, self.state.UNINSTALLING,
                              self.state.UPDATING, self.state.DOWNLOADING]
        if self.current_state in dont_act_in_states:
            return
        if self.game.install_dir and os.path.exists(self.game.install_dir):
            self.update_to_state(self.state.INSTALLED)
        elif self.get_keep_executable_path():
            self.update_to_state(self.state.INSTALLABLE)
        else:
            self.update_to_state(self.state.DOWNLOADABLE)
        check_upd_thread = threading.Thread(target=self.__check_for_update_dlc())
        check_upd_thread.start()

    def update_to_state(self, state):
        self.current_state = state
        if state == self.state.DOWNLOADABLE:
            self.button.set_label(_("download"))
            self.button.set_sensitive(True)
            self.image.set_sensitive(False)
            self.menu_button.hide()
            self.button_cancel.hide()

            self.game.install_dir = ""

            if self.progress_bar:
                self.progress_bar.destroy()

        elif state == self.state.INSTALLABLE:
            self.button.set_label(_("install"))
            self.button.set_sensitive(True)
            self.image.set_sensitive(False)
            self.menu_button.hide()
            self.button_cancel.hide()

            self.game.install_dir = ""

            if self.progress_bar:
                self.progress_bar.destroy()

        elif state == self.state.QUEUED:
            self.button.set_label(_("in queue.."))
            self.button.set_sensitive(False)
            self.image.set_sensitive(False)
            self.menu_button.hide()
            self.button_cancel.show()
            self.__create_progress_bar()

        elif state == self.state.DOWNLOADING:
            self.button.set_label(_("downloading.."))
            self.button.set_sensitive(False)
            self.image.set_sensitive(False)
            self.menu_button.hide()
            self.button_cancel.show()
            if not self.progress_bar:
                self.__create_progress_bar()
            self.progress_bar.show_all()

        elif state == self.state.INSTALLING:
            self.button.set_label(_("installing.."))
            self.button.set_sensitive(False)
            self.image.set_sensitive(True)
            self.menu_button.hide()
            self.button_cancel.hide()

            self.game.install_dir = self.__get_install_dir()

            if self.progress_bar:
                self.progress_bar.destroy()

            self.parent.filter_library()

        elif state == self.state.INSTALLED:
            self.button.set_label(_("play"))
            # self.button.get_style_context().add_class("suggested-action")
            self.button.set_sensitive(True)
            self.image.set_sensitive(True)
            self.menu_button.show()
            self.button_cancel.hide()
            self.game.install_dir = self.__get_install_dir()

            if self.game.platform == "linux":
                self.menu_button_settings.hide()

            if self.progress_bar:
                self.progress_bar.destroy()

            self.menu_button_update.hide()
            self.update_icon.hide()

        elif state == self.state.UNINSTALLING:
            self.button.set_label(_("uninstalling.."))
            self.button.set_sensitive(False)
            self.image.set_sensitive(False)
            self.menu_button.hide()
            self.button_cancel.hide()

            self.game.install_dir = ""

            self.parent.filter_library()

        elif state == self.state.UPDATABLE:
            self.update_icon.show()
            self.update_icon.set_from_file(ICON_UPDATE_PATH)
            self.button.set_label(_("play"))
            self.menu_button.show()
            tooltip_text = "{} (update{})".format(self.game.name, ", Wine" if self.game.platform == "windows" else "")
            self.image.set_tooltip_text(tooltip_text)
            self.menu_button_update.show()
            if self.game.platform == "windows":
                self.wine_icon.set_margin_left(22)

        elif self.current_state == self.state.UPDATING:
            self.button.set_label(_("updating.."))
