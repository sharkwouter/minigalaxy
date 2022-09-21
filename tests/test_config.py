import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch, mock_open

from minigalaxy.config import Config
from minigalaxy.paths import DEFAULT_INSTALL_DIR


class TestConfig(TestCase):

    @patch('os.path.isfile')
    def test_read_config_file(self, mock_isfile: MagicMock):
        mock_isfile.return_value = True
        config_data = \
            """
            {
                "locale": "locale",
                "lang": "lang",
                "view": "view",
                "install_dir": "install_dir",
                "username": "username",
                "keep_installers": true,
                "stay_logged_in": false,
                "use_dark_theme": true,
                "show_hidden_games": true,
                "show_windows_games": true,
                "keep_window_maximized": true,
                "installed_filter": true,
                "create_applications_file": true
            }
            """
        with patch("builtins.open", mock_open(read_data=config_data)):
            config = Config()

        self.assertIsNotNone(config)
        self.assertEqual("locale", config.locale)
        self.assertEqual("lang", config.lang)
        self.assertEqual("view", config.view)
        self.assertEqual("install_dir", config.install_dir)
        self.assertEqual(True, config.keep_installers)
        self.assertEqual(False, config.stay_logged_in)
        self.assertEqual(True, config.use_dark_theme)
        self.assertEqual(True, config.show_hidden_games)
        self.assertEqual(True, config.show_windows_games)
        self.assertEqual(True, config.keep_window_maximized)
        self.assertEqual(True, config.installed_filter)
        self.assertEqual(True, config.create_applications_file)

    @patch('os.path.isfile')
    def test_defaults_if_file_does_not_exist(self, mock_isfile: MagicMock):
        mock_isfile.return_value = False
        config = Config()
        self.assertEqual({}, config._Config__config)

        self.assertEqual("", config.locale)
        self.assertEqual("en", config.lang)
        self.assertEqual("grid", config.view)
        self.assertEqual("", config.username)
        self.assertEqual(DEFAULT_INSTALL_DIR, config.install_dir)
        self.assertEqual(False, config.keep_installers)
        self.assertEqual(True, config.stay_logged_in)
        self.assertEqual(False, config.use_dark_theme)
        self.assertEqual(False, config.show_hidden_games)
        self.assertEqual(False, config.show_windows_games)
        self.assertEqual(False, config.keep_window_maximized)
        self.assertEqual(False, config.installed_filter)
        self.assertEqual(False, config.create_applications_file)

    @patch('os.path.isfile')
    def test_get(self, mock_isfile: MagicMock):
        mock_isfile.return_value = True
        config_data = \
            """
            {
                "lang": "lang"
            }
            """
        with patch("builtins.open", mock_open(read_data=config_data)):
            config = Config()
        lang = config.get("lang")
        self.assertEqual("lang", lang)

    @patch("os.rename")
    @patch('os.path.isfile')
    @patch('os.makedirs')
    def test_create_config(self, mock_makedirs: MagicMock, mock_isfile: MagicMock, mock_rename: MagicMock):
        mock_isfile.return_value = False
        config = Config("/path/config.json")
        with patch("builtins.open", mock_open()):
            config.lang = "lang"
        self.assertEqual("lang", config.lang)
        mock_makedirs.assert_called_once_with("/path", mode=0o700, exist_ok=True)
        mock_rename.assert_called_once_with("/path/config.json.tmp", "/path/config.json")

    @patch("os.rename")
    @patch('os.path.isfile')
    @patch('os.makedirs')
    def test_set(self, mock_makedirs: MagicMock, mock_isfile: MagicMock, mock_rename: MagicMock):
        mock_isfile.return_value = True
        config_data = \
            """
            {
                "lang": "lang"
            }
            """
        with patch("builtins.open", mock_open(read_data=config_data)):
            config = Config("/path/config.json")
            config.set("lang", "lang2")

        self.assertEqual("lang2", config.lang)
        mock_rename.assert_called_once_with("/path/config.json.tmp", "/path/config.json")
