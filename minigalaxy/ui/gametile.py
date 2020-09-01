import shutil
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
import os
import webbrowser
import threading
import subprocess
import re
import urllib.parse
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
    menu_button_store = Gtk.Template.Child()

    state = Enum('state', 'DOWNLOADABLE INSTALLABLE QUEUED DOWNLOADING INSTALLING INSTALLED NOTLAUNCHABLE UNINSTALLING')

    def __init__(self, parent, game, api):
        Gtk.Frame.__init__(self)
        Gtk.StyleContext.add_provider(self.button.get_style_context(),
                                      CSS_PROVIDER,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.parent = parent
        self.game = game
        self.api = api
        self.progress_bar = None
        self.thumbnail_set = False
        self.download = None
        self.current_state = self.state.DOWNLOADABLE

        self.image.set_tooltip_text(self.game.name)

        # Set folder for download installer
        self.download_dir = os.path.join(CACHE_DIR, "download")
        self.download_path = os.path.join(self.download_dir, self.game.get_install_directory_name())

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(Config.get("install_dir"), "installer")
        self.keep_path = os.path.join(self.keep_dir, self.game.get_install_directory_name())

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

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
        elif self.current_state == self.state.INSTALLED:
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
            self.parent.parent.show_eror(
                _("Couldn't open support page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_menu_button_store_clicked")
    def on_menu_button_store(self, widget):
        webbrowser.open(self.gogBaseUrl + self.game.url)

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

    def __download_file(self) -> None:
        Config.set("current_download", self.game.id)
        GLib.idle_add(self.update_to_state, self.state.QUEUED)
        download_info = self.api.get_download_info(self.game)

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
                    # Iff key = 0, denote the file as the executable's path
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
            if os.path.exists(self.keep_path):
                install_game(self.game, self.keep_path, main_window=self.parent.parent)
            else:
                install_game(self.game, self.download_path, main_window=self.parent.parent)
        except (FileNotFoundError, BadZipFile):
            GLib.idle_add(self.update_to_state, self.state.DOWNLOADABLE)
            return
        GLib.idle_add(self.update_to_state, self.state.INSTALLED)

    def __cancel_download(self):
        GLib.idle_add(self.update_to_state, self.state.DOWNLOADABLE)
        GLib.idle_add(self.reload_state)

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
        dont_act_in_states = [self.state.QUEUED, self.state.DOWNLOADING, self.state.INSTALLING, self.state.UNINSTALLING]
        if self.current_state in dont_act_in_states:
            return
        if self.game.install_dir and os.path.exists(self.game.install_dir):
            self.update_to_state(self.state.INSTALLED)
        elif os.path.exists(self.keep_path):
            self.update_to_state(self.state.INSTALLABLE)
        else:
            self.update_to_state(self.state.DOWNLOADABLE)

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

        elif state == self.state.UNINSTALLING:
            self.button.set_label(_("uninstalling.."))
            self.button.set_sensitive(False)
            self.image.set_sensitive(False)
            self.menu_button.hide()
            self.button_cancel.hide()

            self.game.install_dir = ""

            self.parent.filter_library()
