from unittest import TestCase
from unittest.mock import MagicMock, patch, mock_open

from minigalaxy.config import Config
from minigalaxy.paths import DEFAULT_INSTALL_DIR


class TestConfig(TestCase):

    def setUp(self):
        """
        Simple tests of methods contained in config don't have to care about the file.
        They can just use a prepared real instance of Config in "batch_mode" to prevent writes.
        """
        self.config = Config("/no/writes/because/batch/mode")
        self.config.start_batch_edit()

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
        self.assertEqual(False, config.keep_window_maximized)
        self.assertEqual(False, config.installed_filter)
        self.assertEqual(False, config.create_applications_file)
        self.assertEqual([], config.current_downloads)

    def test_config_property_setters(self):
        config = self.config
        config._Config__set_and_write = MagicMock(wraps=config._Config__set_and_write)

        test_properties = [
            ["locale", "", "en_US.UTF-8"],
            ["lang", "en", "pl"],
            ["view", "grid", "list"],
            ["username", "", "username"],
            ["install_dir", DEFAULT_INSTALL_DIR, "/install/dir"],
            ["refresh_token", "", "refresh_token"],
            ["keep_installers", False, True],
            ["stay_logged_in", True, False],
            ["use_dark_theme", False, True],
            ["show_hidden_games", False, True],
            # NOTE: platform_mode getter/setter work on incompatible types
            # can not be tested here with the regular simple test loop
            # ["platform_mode", ["linux"], "windows,linux"]
            ["keep_window_maximized", False, True],
            ["installed_filter", False, True],
            ["create_applications_file", False, True],
            ["current_downloads", [], [1, 2, 3]],
            ["paused_downloads", {}, {"/some/file": 55}]
        ]

        for prop in test_properties:
            key = prop[0]
            current_value = prop[1]
            new_value = prop[2]
            self.assertEqual(current_value, getattr(config, key), f"Property '{key}' default not as expected")
            setattr(config, key, new_value)
            self.assertEqual(new_value, getattr(config, key, f"Property '{key}' setter or getter not not working"))

        err_msg = f"Expected {len(test_properties)} calls of Config.__set_and_write"
        self.assertEqual(len(test_properties), config._Config__set_and_write.call_count, err_msg)

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

    def test_add_ongoing_download(self):
        self.assertEqual([], self.config.current_downloads)

        self.config.add_ongoing_download("TESTID")
        self.assertEqual(["TESTID"], self.config.current_downloads)

        # not added a second time
        self.config.add_ongoing_download("TESTID")
        self.assertEqual(1, len(self.config.current_downloads))

    def test_remove_ongoing_download(self):
        self.assertEqual([], self.config.current_downloads)

        # removing something that is not contained should just be silently ignored
        self.config.remove_ongoing_download("UNKNOWN-ID")

        self.config.add_ongoing_download("TESTID")
        self.config.remove_ongoing_download("TESTID")
        self.assertEqual([], self.config.current_downloads)

    def test_add_paused_download(self):
        self.assertEqual({}, self.config.paused_downloads)

        self.config.add_paused_download("/test/file", 12)
        self.assertEqual({"/test/file": 12}, self.config.paused_downloads)

    def test_remove_paused_download(self):
        self.assertEqual({}, self.config.paused_downloads)

        # removing something that is not contained should just be silently ignored
        self.config.remove_paused_download("/unknown/file")

        self.config.add_paused_download("/known/file", 42)
        self.config.remove_paused_download("/known/file")
        self.assertEqual({}, self.config.paused_downloads)

    def test_platform_mode(self):
        # default value
        self.assertEqual(["linux"], self.config.platform_mode)

        # set new value as string
        self.config.platform_mode = "windows,linux"
        self.assertEqual(["windows", "linux"], self.config.platform_mode)

        # platform mode also (optionally) takes a list of strings for convenience in code
        # this test can't use the getter, because that automatically wraps back to list
        self.config.platform_mode = ["linux", "windows"]
        self.assertEqual("linux,windows", self.config._Config__config["platform_mode"])
