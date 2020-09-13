import os
from zipfile import BadZipFile
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from minigalaxy.paths import UI_DIR

@Gtk.Template.from_file(os.path.join(UI_DIR, "download.ui"))
class Download(Gtk.Box):
    __gtype_name__ = "Download"

    title = Gtk.Template.Child()
    information = Gtk.Template.Child()
    progress = Gtk.Template.Child()
    cancel = Gtk.Template.Child()

    def __init__(self, url, save_location, finish_func=None, progress_func=None, cancel_func=None, number=1, out_of_amount=1, name=""):
        Gtk.Box.__init__(self)
        self.name = name
        self.url = url
        self.save_location = save_location
        self.__finish_func = finish_func
        self.__progress_func = progress_func
        self.__cancel_func = cancel_func
        self.number = number
        self.out_of_amount = out_of_amount

        if name:
            self.title.set_text(self.name)
            self.show_all()

    def set_progress(self, percentage: int) -> None:
        if self.__progress_func:
            if self.out_of_amount > 1:
                # Change the percentage based on which number we are
                progress_start = 100/self.out_of_amount*(self.number-1)
                percentage = progress_start + percentage/self.out_of_amount
            self.__progress_func(percentage)

    def finish(self):
        if self.__finish_func:
            try:
                self.__finish_func()
            except (FileNotFoundError, BadZipFile):
                self.cancel()

    @Gtk.Template.Callback("on_cancel_clicked")
    def cancel(self, button=None):
        if self.__cancel_func:
            self.__cancel_func()
            GLib.idle_add(self.hide)
