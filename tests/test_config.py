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
                "refresh_token": "refresh_token",
                "keep_installers": true,
                "stay_logged_in": false,
                "use_dark_theme": true,
                "show_hidden_games": true,
                "show_windows_games": true,
                "keep_window_maximized": true,
                "installed_filter": true,
                "create_applications_file": true,
                "current_downloads": [1, 2, 3]
            }
            """
        with patch("builtins.open", mock_open(read_data=config_data)):
            config = Config()

        self.assertIsNotNone(config)
        self.assertEqual("locale", config.locale)
        self.assertEqual("lang", config.lang)
        self.assertEqual("view", config.view)
        self.assertEqual("install_dir", config.install_dir)
        self.assertEqual("username", config.username)
        self.assertEqual("refresh_token", config.refresh_token)
        self.assertEqual(True, config.keep_installers)
        self.assertEqual(False, config.stay_logged_in)
        self.assertEqual(True, config.use_dark_theme)
        self.assertEqual(True, config.show_hidden_games)
        self.assertEqual(True, config.show_windows_games)
        self.assertEqual(True, config.keep_window_maximized)
        self.assertEqual(True, config.installed_filter)
        self.assertEqual(True, config.create_applications_file)
        self.assertEqual([1, 2, 3], config.current_downloads)

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
        self.assertEqual("", config.refresh_token)
        self.assertEqual(False, config.keep_installers)
        self.assertEqual(True, config.stay_logged_in)
        self.assertEqual(False, config.use_dark_theme)
        self.assertEqual(False, config.show_hidden_games)
        self.assertEqual(False, config.show_windows_games)
        self.assertEqual(False, config.keep_window_maximized)
        self.assertEqual(False, config.installed_filter)
        self.assertEqual(False, config.create_applications_file)
        self.assertEqual([], config.current_downloads)

    @patch("os.remove")
    @patch("os.path.isfile")
    def test_invalid_config_file_is_deleted(self, mock_isfile: MagicMock, mock_remove: MagicMock):
        mock_isfile.return_value = True
        filename = "/this/is/a/test"
        config_data = \
            """
            {
                "locale": "locale",
            """
        with patch("builtins.open", mock_open(read_data=config_data)):
            config = Config(filename)

        mock_remove.assert_called_once_with(filename)

        self.assertEqual("", config.locale)
        self.assertEqual("en", config.lang)
        self.assertEqual("grid", config.view)
        self.assertEqual("", config.username)
        self.assertEqual(DEFAULT_INSTALL_DIR, config.install_dir)
        self.assertEqual("", config.refresh_token)
        self.assertEqual(False, config.keep_installers)
        self.assertEqual(True, config.stay_logged_in)
        self.assertEqual(False, config.use_dark_theme)
        self.assertEqual(False, config.show_hidden_games)
        self.assertEqual(False, config.show_windows_games)
        self.assertEqual(False, config.keep_window_maximized)
        self.assertEqual(False, config.installed_filter)
        self.assertEqual(False, config.create_applications_file)
        self.assertEqual([], config.current_downloads)

    @patch("os.path.isfile")
    def test_config_property_setters(self, mock_isfile: MagicMock):
        mock_isfile.return_value = True
        filename = "/this/is/a/test"
        config_data = "{}"
        with patch("builtins.open", mock_open(read_data=config_data)):
            config = Config(filename)
            config._Config__write = MagicMock()

        self.assertEqual("", config.locale)
        config.locale = "en_US.UTF-8"
        self.assertEqual("en_US.UTF-8", config.locale)

        config._Config__write.assert_called_once()

        self.assertEqual("en", config.lang)
        config.lang = "pl"
        self.assertEqual("pl", config.lang)

        self.assertEqual("grid", config.view)
        config.view = "list"
        self.assertEqual("list", config.view)

        self.assertEqual("", config.username)
        config.username = "username"
        self.assertEqual("username", config.username)

        self.assertEqual(DEFAULT_INSTALL_DIR, config.install_dir)
        config.install_dir = "/install/dir"
        self.assertEqual("/install/dir", config.install_dir)

        self.assertEqual("", config.refresh_token)
        config.refresh_token = "refresh_token"
        self.assertEqual("refresh_token", config.refresh_token)

        self.assertEqual(False, config.keep_installers)
        config.keep_installers = True
        self.assertEqual(True, config.keep_installers)

        self.assertEqual(True, config.stay_logged_in)
        config.stay_logged_in = False
        self.assertEqual(False, config.stay_logged_in)

        self.assertEqual(False, config.use_dark_theme)
        config.use_dark_theme = True
        self.assertEqual(True, config.use_dark_theme)

        self.assertEqual(False, config.show_hidden_games)
        config.show_hidden_games = True
        self.assertEqual(True, config.show_hidden_games)

        self.assertEqual(False, config.show_windows_games)
        config.show_windows_games = True
        self.assertEqual(True, config.show_windows_games)

        self.assertEqual(False, config.keep_window_maximized)
        config.keep_window_maximized = True
        self.assertEqual(True, config.keep_window_maximized)

        self.assertEqual(False, config.installed_filter)
        config.installed_filter = True
        self.assertEqual(True, config.installed_filter)

        self.assertEqual(False, config.create_applications_file)
        config.create_applications_file = True
        self.assertEqual(True, config.create_applications_file)

        self.assertEqual([], config.current_downloads)
        config.current_downloads = [1, 2, 3]
        self.assertEqual([1, 2, 3], config.current_downloads)

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
