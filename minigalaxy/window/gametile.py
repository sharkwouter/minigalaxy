import shutil

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
import requests
import os
import threading
import subprocess


@Gtk.Template.from_file("data/ui/gametile.ui")
class GameTile(Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()

    state = None

    def __init__(self, game=None, api=None):
        Gtk.Frame.__init__(self)
        self.game = game
        self.api = api
        self.progress_bar = None

        self.image.set_tooltip_text(self.game.name)

        self.__load_state()

        image_thread = threading.Thread(target=self.__load_image)
        image_thread.daemon = True
        image_thread.start()

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        if self.state:
            return
        self.__create_progress_bar()
        widget.set_sensitive(False)
        widget.set_label("downloading...")
        download_thread = threading.Thread(target=self.__download_file)
        download_thread.start()

    def __load_image(self) -> None:
        # image_url = "https:" + self.image_url + "_392.jpg" #This is the bigger image size
        image_url = "https:{}_196.jpg".format(self.game.image_url)
        filename = "data/images/{}.jpg".format(self.game.id)
        if not os.path.isfile(filename):
            download = requests.get(image_url)
            with open(filename, "wb") as writer:
                writer.write(download.content)
                writer.close()
        self.image.set_from_file(filename)

    def __download_file(self) -> None:
        download_info = self.api.get_download_info(self.game)
        file_url = download_info["downlink"]
        filename = "data/download/{}.sh".format(self.game.id)
        data = requests.get(file_url, stream=True)
        handler = open(filename, "wb")

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
                    self.progress_bar.set_fraction(percentage)
                    self.progress_bar.show_all()
                    chunk_count = 0
        handler.close()
        self.progress_bar.destroy()
        self.__install_game()
        self.__load_state()

    def __install_game(self) -> None:
        outputpath = "data/installed/{}/".format(self.game.name)
        temp_dir = "temp/{}".format(self.game.id)

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        subprocess.call(["unzip", "-qq", "data/download/{}.sh".format(self.game.id), "data/noarch/*", "-d",
                         temp_dir])
        os.rename(os.path.join(temp_dir, "data/noarch"), outputpath)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def __create_progress_bar(self) -> None:
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_halign(Gtk.Align.CENTER)
        self.progress_bar.set_size_request(196, -1)
        self.progress_bar.set_hexpand(False)
        self.progress_bar.set_vexpand(False)
        self.set_center_widget(self.progress_bar)
        self.progress_bar.set_fraction(0.0)
        self.show()

    def __load_state(self) -> None:
        filename = "data/installed/{}/start.sh".format(self.game.name)
        if os.path.isfile(filename):
            self.state = "installed"
            self.button.set_label("play")
            self.button.set_sensitive(True)
            self.button.connect("clicked", self.__start_game)
        else:
            self.button.set_label("download")

        self.button.show()

    def __start_game(self, widget) -> subprocess:
        filename = "data/installed/{}/start.sh".format(self.game.name)
        return subprocess.run([filename])

    def __lt__(self, other):
        names = [str(self), str(other)]
        names.sort()
        if names[0] == str(self):
            return True
        return False
