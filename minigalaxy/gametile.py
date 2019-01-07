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
        self.button.set_label(name)
        self.image_url = image
        image_threat = threading.Thread(target=self.__load_image)
        image_threat.start()
        #self.__load_image(image)
        #self.show_all()

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget):
        print("button")

    def __load_image(self):
        image_url = "https:" + self.image_url + "_392.jpg"
        filename = "data/images/" + str(self.id) + ".jpg"
        if not os.path.isfile(filename):
            download = requests.get(image_url)
            with open(filename, "wb") as writer:
                writer.write(download.content)
                writer.close()
        self.image.set_from_file(filename)
