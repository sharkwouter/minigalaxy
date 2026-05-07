from unittest.mock import MagicMock


class MockGiRepository:

    class Gtk:
        Widget = MagicMock()
        Settings = MagicMock()
        ResponseType = MagicMock()

        class ApplicationWindow:
            def __init__(self, title):
                pass

            set_default_icon_list = MagicMock()
            show_all = MagicMock()

        class Box:
            pass

        class Dialog:
            pass

        class Template:
            def __init__(self, string=None):
                pass

            @classmethod
            def from_file(cls, lib_file):
                return cls()

            @classmethod
            def Child(cls):
                return MagicMock()

            Callback = MagicMock()

            def __call__(self, func):
                def passthrough(*args, **kwargs):
                    return func(*args, **kwargs)
                return passthrough

        class Viewport:
            pass

    class Gdk:
        pass

    GdkPixbuf = MagicMock()

    class Gio:
        pass

    class GLib:
        pass

    Notify = MagicMock()
