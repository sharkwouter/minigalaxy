import shutil
import zipfile

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
import requests
import json
import os
import threading
import subprocess
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, UI_DIR


@Gtk.Template.from_file(os.path.join(UI_DIR, "gametile.ui"))
class GameTile(Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()

    def __init__(self, parent, game=None, api=None, install_dir=""):
        Gtk.Frame.__init__(self)
        self.parent = parent
        self.game = game
        self.api = api
        self.progress_bar = None
        self.installed = False
        self.install_dir = install_dir
        self.busy = False

        self.image.set_tooltip_text(self.game.name)

        self.download_dir = os.path.join(CACHE_DIR, "download")
        self.download_path = os.path.join(self.download_dir, "{}.sh".format(self.game.name))
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        self.load_state()

        image_thread = threading.Thread(target=self.__load_image)
        image_thread.start()

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        if self.busy:
            return
        if self.installed:
            self.__start_game()
        else:
            self.busy = True
            self.__create_progress_bar()
            widget.set_sensitive(False)
            widget.set_label(_("downloading..."))
            download_thread = threading.Thread(target=self.__download_file)
            download_thread.start()

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        self.menu_button.hide()
        self.button.set_sensitive(False)
        self.button.set_label(_("uninstalling.."))
        uninstall_thread = threading.Thread(target=self.__uninstall_game)
        uninstall_thread.start()

    @Gtk.Template.Callback("on_menu_button_open_clicked")
    def on_menu_button_open_files(self, widget):
        subprocess.call(["xdg-open", self.__get_install_dir()])

    def __load_image(self) -> None:
        image_thumbnail_dir = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
        image_install_dir = os.path.join(self.__get_install_dir(), "thumbnail.jpg")

        # Set the image to the one in the game directory in offline mode
        if self.game.id == 0:
            if os.path.isfile(image_install_dir):
                GLib.idle_add(self.image.set_from_file, image_install_dir)
            return

        # Download the image if it doesn't exist yet
        if not os.path.isfile(image_thumbnail_dir):
            image_url = "https:{}_196.jpg".format(self.game.image_url)
            download = requests.get(image_url)
            with open(image_thumbnail_dir, "wb") as writer:
                writer.write(download.content)
                writer.close()

        # Copy the image to the game directory if not there yet
        if not os.path.isfile(image_install_dir) and os.path.isdir(self.__get_install_dir()):
            shutil.copy2(image_thumbnail_dir, image_install_dir)

        GLib.idle_add(self.image.set_from_file, image_thumbnail_dir)

    def __download_file(self) -> None:
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        download_info = self.api.get_download_info(self.game)
        file_url = download_info["downlink"]
        data = requests.get(file_url, stream=True)
        handler = open(self.download_path, "wb")

        total_size = int(data.headers.get('content-length'))
        downloaded_size = 0
        chunk_count = 0
        for chunk in data.iter_content(chunk_size=4096):
            if chunk:
                chunk_count += 1
                handler.write(chunk)
                downloaded_size += len(chunk)
                # Only update the progress bar every 2 megabytes
                if chunk_count == 4000:
                    percentage = downloaded_size / total_size
                    GLib.idle_add(self.progress_bar.set_fraction, percentage)
                    chunk_count = 0
        handler.close()
        GLib.idle_add(self.progress_bar.destroy)
        GLib.idle_add(self.button.set_label, _("installing.."))
        self.__install_game()
        self.busy = False
        GLib.idle_add(self.load_state)
        GLib.idle_add(self.button.set_sensitive, True)
        GLib.idle_add(self.parent.filter_library)

    def __install_game(self) -> None:
        # Make a temporary empty directory for extracting the installer
        temp_dir = os.path.join(CACHE_DIR, "extract/{}".format(self.game.id))
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir)

        # Extract the installer
        with zipfile.ZipFile(self.download_path) as archive:
            for member in archive.namelist():
                file = archive.getinfo(member)
                archive.extract(file, temp_dir)
                # Set permissions
                attr = file.external_attr >> 16
                os.chmod(os.path.join(temp_dir, member), attr)

        # Make sure the install directory exists
        library_dir = self.api.config.get("install_dir")
        if not os.path.exists(library_dir):
            os.makedirs(library_dir)

        # Copy the game files into the correct directory
        shutil.move(os.path.join(temp_dir, "data/noarch"), self.__get_install_dir())
        shutil.copyfile(
            os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id)),
            os.path.join(self.__get_install_dir(), "thumbnail.jpg"),
        )

        # Remove the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        os.remove(self.download_path)

    def __uninstall_game(self):
        shutil.rmtree(self.__get_install_dir(), ignore_errors=True)
        GLib.idle_add(self.load_state)
        GLib.idle_add(self.button.set_sensitive, True)

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
        if not self.install_dir or not os.path.isdir(self.install_dir):
            self.install_dir = os.path.join(self.api.config.get("install_dir"), self.game.name)
        return self.install_dir

    def __get_executable_path(self):
        return os.path.join(self.__get_install_dir(), "start.sh")

    def load_state(self) -> None:
        if self.busy:
            return
        if os.path.isfile(os.path.join(self.__get_install_dir(), "gameinfo")):
            self.installed = True
            self.button.set_label(_("play"))
            self.menu_button.show()
        else:
            self.installed = False
            self.button.set_label(_("download"))
            self.menu_button.hide()

    def __start_game(self) -> subprocess:
        error_message = ""
        game = None
        try:
            game = subprocess.Popen([self.__get_executable_path()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            # Try the goggame-*.info file to figure out what the binary is
            info_file = os.path.join(self.__get_install_dir(), "game/goggame-{}.info".format(self.game.id))
            if os.path.isfile(info_file):
                with open(info_file, 'r') as file:
                    info = json.loads(file.read())
                    print(info)
                    file.close()
                if info:
                    binary_dir = os.path.join(self.__get_install_dir(), "game")
                    os.chdir(binary_dir)
                    exec_command = "./{}".format(info["playTasks"][0]["path"])
                    game = subprocess.Popen([exec_command], stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            else:
                error_message = _("No executable was found in {}").format(self.__get_install_dir())

        if game:
            try:
                game.wait(timeout=float(3))
            except subprocess.TimeoutExpired:
                return game
        else:
            error_message = _("Couldn't start subprocess")

        # Now deal with the error we've received
        if not error_message:
            stdout, stderror = game.communicate()
            error_message = stderror.decode("utf-8")
            if not error_message:
                error_message = _("No error message was returned")

        error_text = _("Failed to start {}:").format(self.game.name)
        print(error_text)
        print(error_message)
        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=error_text
        )
        dialog.format_secondary_text(error_message)
        dialog.run()
        dialog.destroy()

    def __lt__(self, other):
        names = [str(self), str(other)]
        names.sort()
        if names[0] == str(self):
            return True
        return False
