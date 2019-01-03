import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gui.mainwindow import MainWindow
from api.gog import GOGAPI


def main():
    gog = GOGAPI()
    window = MainWindow("python-gog-client", gog)
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
