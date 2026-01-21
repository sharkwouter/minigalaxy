import gi
from minigalaxy.ui.data import get_data_file as _ui_data_file

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf  # noqa: E402,F401
gi.require_version('Notify', '0.7')
from gi.repository import Notify  # noqa: E402,F401


def load_pixbuf(file_name: str) -> GdkPixbuf.Pixbuf:
    """
    Load a data file as a pixbuf.
    Not relying on Gtk's file load system.
    """
    loader = GdkPixbuf.PixbufLoader()
    loader.write(_ui_data_file(file_name).read_bytes())
    loader.close()
    return loader.get_pixbuf()


def load_ui(file_name: str) -> str:
    """
    Read a UI data file as utf-8 encoded text.
    """
    return _ui_data_file(file_name).read_text(encoding='utf-8')
