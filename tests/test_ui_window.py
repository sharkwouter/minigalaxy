import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch
from simplejson.errors import JSONDecodeError

m_gtk = MagicMock()
m_gi = MagicMock()
m_library = MagicMock()
m_preferences = MagicMock()
m_login = MagicMock()
m_about = MagicMock()


class UnitTestGtkTemplate:

    def __init__(self):
        self.Child = m_gtk

    def from_file(self, lib_file):
        def passthrough(func):
            def passthrough2():
                return func()
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


u_gi_repository = UnitTestGiRepository()
sys.modules['gi.repository'] = u_gi_repository
sys.modules['gi'] = m_gi
sys.modules['minigalaxy.ui.library'] = m_library
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.login'] = m_login
sys.modules['minigalaxy.ui.about'] = m_about
sys.modules['minigalaxy.ui.gtk'] = u_gi_repository
from minigalaxy.ui.window import Window  # noqa: E402


class TestWindow(TestCase):
    def test1_init(self):
        with patch('minigalaxy.ui.window.Api.can_connect', return_value=False):
            test_window = Window()
            exp = True
            obs = test_window.offline
            self.assertEqual(exp, obs)

    def test2_init(self):
        with patch('minigalaxy.ui.window.Api.can_connect', return_value=True):
            with patch('minigalaxy.ui.window.Api.authenticate', return_value=True):
                test_window = Window()
                exp = False
                obs = test_window.offline
                self.assertEqual(exp, obs)
                self.assertEqual(test_window.api.authenticate.called, True)

    def test3_init(self):
        with patch('minigalaxy.ui.window.Api.authenticate', side_effect=JSONDecodeError(msg='mock', doc='mock', pos=0)):
            test_window = Window()
            exp = True
            obs = test_window.offline
            self.assertEqual(exp, obs)


del sys.modules['gi']
del sys.modules['gi.repository']
del sys.modules['minigalaxy.ui.library']
del sys.modules['minigalaxy.ui.preferences']
del sys.modules['minigalaxy.ui.login']
del sys.modules['minigalaxy.ui.about']
del sys.modules['minigalaxy.ui.gtk']
