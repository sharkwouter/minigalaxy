import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch
from simplejson.errors import JSONDecodeError

from MockGiRepository import MockGiRepository

m_gtk = MagicMock()
m_gi = MagicMock()
m_library = MagicMock()
m_download_list = MagicMock()
m_preferences = MagicMock()
m_login = MagicMock()
m_about = MagicMock()
m_categoryfilters = MagicMock()

sys.modules['gi.repository'] = MockGiRepository()
sys.modules['gi'] = m_gi
sys.modules['minigalaxy.ui.download_list'] = m_download_list
sys.modules['minigalaxy.ui.library'] = m_library
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.login'] = m_login
sys.modules['minigalaxy.ui.about'] = m_about
sys.modules['minigalaxy.ui.categoryfilters'] = m_categoryfilters
from minigalaxy.ui.window import Window  # noqa: E402


class TestWindow(TestCase):
    def test1_init(self):
        with patch('minigalaxy.ui.window.Api.can_connect', return_value=False):
            config = MagicMock()
            config.locale = "en_US.UTF-8"
            config.keep_window_maximized = False
            api = MagicMock()
            api.can_connect.return_value = False
            test_window = Window(api=api, config=config, download_manager=MagicMock())
            test_window.load_library()
            exp = True
            obs = test_window.offline
            self.assertEqual(exp, obs)

    def test2_init(self):
        config = MagicMock()
        config.locale = "en_US.UTF-8"
        config.keep_window_maximized = False
        api = MagicMock()
        api.authenticate.return_value = True
        test_window = Window(api=api, config=config, download_manager=MagicMock())
        test_window.load_library()
        exp = False
        obs = test_window.offline
        self.assertEqual(exp, obs)
        api.authenticate.assert_called_once()

    def test3_init(self):
        config = MagicMock()
        config.locale = "en_US.UTF-8"
        config.keep_window_maximized = False
        api = MagicMock()
        api.authenticate.side_effect = JSONDecodeError(msg='mock', doc='mock', pos=0)
        test_window = Window(api=api, config=config, download_manager=MagicMock())
        test_window.load_library()
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
