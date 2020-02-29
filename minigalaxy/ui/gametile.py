import shutil
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import webbrowser
import threading
import subprocess
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, UI_DIR
from minigalaxy.config import Config
from minigalaxy.download import Download
from minigalaxy.download_manager import DownloadManager
from minigalaxy.launcher import start_game
from minigalaxy.installer import uninstall_game, install_game


@Gtk.Template.from_file(os.path.join(UI_DIR, "gametile.ui"))
class GameTile(Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()

    def __init__(self, parent, game, api):
        Gtk.Frame.__init__(self)
        self.parent = parent
        self.game = game
        self.api = api
        self.progress_bar = None
        self.busy = False
        self.thumbnail_set = False

        self.image.set_tooltip_text(self.game.name)

        # Set folder for download installer
        self.download_dir = os.path.join(CACHE_DIR, "download")
        self.download_path = os.path.join(self.download_dir, "{}.sh".format(self.game.name))

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(Config.get("install_dir"), "installer")
        self.keep_path = os.path.join(self.keep_dir, "{}.sh".format(self.game.name))

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        self.load_state()

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        if self.busy:
            return
        if self.game.install_dir:
            start_game(self.game, self.parent)
        else:
            self.busy = True
            self.__create_progress_bar()
            widget.set_sensitive(False)
            widget.set_label(_("downloading..."))
            download_thread = threading.Thread(target=self.__download_file)
            download_thread.start()

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        message_dialog = Gtk.MessageDialog(parent=self.parent.parent,
                                           flags=Gtk.DialogFlags.MODAL,
                                           message_type=Gtk.MessageType.WARNING,
                                           buttons=Gtk.ButtonsType.OK_CANCEL,
                                           message_format=_("Are you sure to uninstall %s" % self.game.name))
        response = message_dialog.run()

        if response == Gtk.ResponseType.OK:
            self.menu_button.hide()
            self.button.set_sensitive(False)
            self.button.set_label(_("uninstalling.."))
            uninstall_thread = threading.Thread(target=self.__uninstall_game)
            uninstall_thread.start()
            message_dialog.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            message_dialog.destroy()

    @Gtk.Template.Callback("on_menu_button_open_clicked")
    def on_menu_button_open_files(self, widget):
        subprocess.call(["xdg-open", self.__get_install_dir()])

    @Gtk.Template.Callback("on_menu_button_support_clicked")
    def on_menu_button_support(self, widget):
        try:
            webbrowser.open(self.api.get_info(self.game)['links']['support'], new=2)
        except:
            dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.ERROR,
                parent=self.parent.parent,
                modal=True,
                buttons=Gtk.ButtonsType.OK,
                text=_("Couldn't open support page")
            )
            dialog.format_secondary_text(_("Please check your internet connection"))
            dialog.run()
            dialog.destroy()

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
        download_info = self.api.get_download_info(self.game)
        file_url = download_info["downlink"]
        download = Download(file_url, self.download_path, self.__finish_download, progress_func=self.set_progress, cancel_func=self.__cancel_download)
        DownloadManager.download(download)

    def __finish_download(self):
        GLib.idle_add(self.progress_bar.destroy)
        GLib.idle_add(self.button.set_label, _("installing.."))
        self.game.install_dir = self.__get_install_dir()
        install_game(self.game, self.download_path)
        self.busy = False
        GLib.idle_add(self.load_state)
        GLib.idle_add(self.button.set_sensitive, True)
        GLib.idle_add(self.parent.filter_library)

    def __cancel_download(self):
        GLib.idle_add(self.progress_bar.destroy)
        self.busy = False
        GLib.idle_add(self.load_state)
        GLib.idle_add(self.button.set_sensitive, True)

    def set_progress(self, percentage: int):
        GLib.idle_add(self.progress_bar.set_fraction, percentage/100)

    def __uninstall_game(self):
        uninstall_game(self.game)
        GLib.idle_add(self.load_state)
        GLib.idle_add(self.button.set_sensitive, True)
        self.game.install_dir = ""

    def __create_progress_bar(self) -> None:
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_halign(Gtk.Align.CENTER)
        self.progress_bar.set_size_request(196, -1)
        self.progress_bar.set_hexpand(False)
        self.progress_bar.set_vexpand(False)
        self.set_center_widget(self.progress_bar)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.show_all()

    def __get_install_dir(self):
        if self.game.install_dir:
            return self.game.install_dir
        return os.path.join(Config.get("install_dir"), self.game.get_stripped_name())

    def load_state(self) -> None:
        if self.busy:
            return
        if not self.thumbnail_set:
            self.thumbnail_set = self.load_thumbnail()
        if os.path.isfile(os.path.join(self.__get_install_dir(), "gameinfo")):
            self.game.install_dir = self.__get_install_dir()
            self.image.set_sensitive(True)
            self.button.set_label(_("play"))
            self.menu_button.show()
        elif os.path.exists(self.keep_path):
            self.image.set_sensitive(False)
            self.button.set_label(_("install"))
            self.menu_button.hide()
        else:
            self.image.set_sensitive(False)
            self.button.set_label(_("download"))
            self.menu_button.hide()
