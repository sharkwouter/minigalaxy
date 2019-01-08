import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
import requests
import os
import threading

@Gtk.Template.from_file("data/ui/gametile.ui")
class GameTile(Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()

    def __init__(self, id=None, name=None, image=None, api=None):
        Gtk.Frame.__init__(self)
        self.id = id
        self.name = name
        self.api = api
        self.button.set_label("download")
        self.image_url = image
        self.progress_bar = None
        image_thread = threading.Thread(target=self.__load_image)
        image_thread.daemon = True
        image_thread.start()

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget):
        self.__create_progress_bar()
        download_thread = threading.Thread(target=self.__download_file)
        download_thread.start()

    def __load_image(self):
        #image_url = "https:" + self.image_url + "_392.jpg" #This is the bigger image size
        image_url = "https:" + self.image_url + "_196.jpg"
        filename = "data/images/" + str(self.id) + ".jpg"
        if not os.path.isfile(filename):
            download = requests.get(image_url)
            with open(filename, "wb") as writer:
                writer.write(download.content)
                writer.close()
        self.image.set_from_file(filename)

    def __download_file(self):
        download_info = self.api.get_download_info(self.id)
        file_url = download_info["downlink"]
        filename = "data/download/{}.sh".format(self.id)
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
                if chunk_count == 1000:
                    percentage = downloaded_size / total_size
                    self.progress_bar.set_fraction(percentage)
                    self.progress_bar.show_all()
                    chunk_count = 0
        self.set_center_widget(None)
        handler.close()

    def __create_progress_bar(self):
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_halign(Gtk.Align.CENTER)
        self.progress_bar.set_size_request(196, -1)
        self.progress_bar.set_hexpand(False)
        self.progress_bar.set_vexpand(False)
        self.set_center_widget(self.progress_bar)
        self.progress_bar.set_fraction(0.0)
        self.show_all()

