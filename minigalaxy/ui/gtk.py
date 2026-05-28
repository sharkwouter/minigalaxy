import gi
from minigalaxy.resources import get_ui_data_file as _ui_data_file

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf  # noqa: E402,F401
gi.require_version('Notify', '0.7')
from gi.repository import Notify  # noqa: E402,F401

# cache loaded images to prevent having to reload them from disk all the time
PIXBUF_CACHE = {}


def load_pixbuf(file_name: str, cache_file=True) -> GdkPixbuf.Pixbuf:
    """
    Load a data file as a pixbuf. Doesn't rely on Gtk's file load system.
    By default, the file is cached for repeated usage. This is most useful for small icons
    which appear multiple times, e.g. once per game.

    The caching can also be disabled for one call by passing cache_file=False
    """
    if file_name in PIXBUF_CACHE and cache_file:
        return PIXBUF_CACHE[file_name]

    loader = GdkPixbuf.PixbufLoader()
    try:
        loader.write(_ui_data_file(file_name).read_bytes())
    finally:
        loader.close()

    pb = loader.get_pixbuf()
    if cache_file:
        PIXBUF_CACHE[file_name] = pb

    return pb


def load_ui(file_name: str) -> str:
    """Read a UI data file as utf-8 encoded text."""
    return _ui_data_file(file_name).read_text(encoding='utf-8')


def load_scaled_pixbuf(file_name: str, size: int, cache_file=True):
    """
    Load a data file as a pixbuf and immediately scale it to the given proportions.
    By default, both the original and the scaled pixbuf will be placed in a resource cache for repeated usage.
    This saves memory and increases load speed.
    """
    cache_name = "{}_{}x{}".format(file_name, size, size)
    if cache_name in PIXBUF_CACHE and cache_file:
        return PIXBUF_CACHE[cache_name]

    pb = scale_pixbuf(load_pixbuf(file_name, cache_file), size)
    if cache_file:
        PIXBUF_CACHE[cache_name] = pb
    return pb


def scale_pixbuf(pixbuf: GdkPixbuf, size):
    """Simple helper to scale squared PixBufs (icons) up or down."""
    return pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
