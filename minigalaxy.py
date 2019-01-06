import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from minigalaxy.window import Window
from minigalaxy.api import Api


def main():
    api = Api()
    window = Window("MiniGalaxy", api)
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
