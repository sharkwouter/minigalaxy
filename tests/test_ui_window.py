import sys
from unittest import TestCase, skip
from unittest.mock import MagicMock

m_gtk = MagicMock()
m_gi = MagicMock()
m_library = MagicMock()
m_preferences = MagicMock()
m_login = MagicMock()
m_about = MagicMock()
m_categoryfilters = MagicMock()
m_properties = MagicMock()
m_information = MagicMock()
m_game = MagicMock()


class UnitTestGtkTemplate:

    def __init__(self):
        self.Child = m_gtk

    def from_file(self, lib_file):
        def passthrough(func):
            def passthrough2(*args, **kwargs):
                return func(*args, **kwargs)
            return passthrough2
        return passthrough

    Callback = MagicMock()


class UnitTestGiRepository:

    class Gtk:
        Template = UnitTestGtkTemplate()
        Widget = MagicMock()
        Settings = MagicMock()
        ResponseType = MagicMock()

        class ApplicationWindow:
            def __init__(self, title):
                pass

            set_default_icon_list = MagicMock()
            show_all = MagicMock()

    Gdk = MagicMock()
    GdkPixbuf = MagicMock()
    Gio = MagicMock()
    GLib = MagicMock
    Notify = MagicMock()


u_gi_repository = UnitTestGiRepository()
sys.modules['gi.repository'] = u_gi_repository
sys.modules['gi'] = m_gi
sys.modules['minigalaxy.ui.library'] = m_library
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.login'] = m_login
sys.modules['minigalaxy.ui.about'] = m_about
sys.modules['minigalaxy.ui.gtk'] = u_gi_repository
sys.modules['minigalaxy.ui.categoryfilters'] = m_categoryfilters
sys.modules['minigalaxy.ui.properties'] = m_properties
sys.modules['minigalaxy.ui.information'] = m_information
sys.modules['minigalaxy.ui.game'] = m_game
# from minigalaxy.ui.window import Window  # noqa: E402


class TestWindow(TestCase):
    @skip("no significant logic to test left in constructor")
    def test1_init(self):
        pass


del sys.modules['gi']
del sys.modules['gi.repository']
del sys.modules['minigalaxy.ui.library']
del sys.modules['minigalaxy.ui.preferences']
del sys.modules['minigalaxy.ui.login']
del sys.modules['minigalaxy.ui.about']
del sys.modules['minigalaxy.ui.gtk']
del sys.modules['minigalaxy.ui.categoryfilters']
del sys.modules['minigalaxy.ui.properties']
del sys.modules['minigalaxy.ui.information']
del sys.modules['minigalaxy.ui.game']
