import sys
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch, mock_open
from minigalaxy.config import DEFAULT_CONFIGURATION
JSON_DEFAULT_CONFIGURATION = str(DEFAULT_CONFIGURATION).replace("'", "\"").replace("False", "false").replace("True", "true")

m_thread = MagicMock()
sys.modules['threading'] = m_thread


class TestConfig(TestCase):
    @mock.patch('os.path.exists')
    def test_get(self, mock_isfile):
        mock_isfile.return_value = True
        config = JSON_DEFAULT_CONFIGURATION
        with patch("builtins.open", mock_open(read_data=config)):
            from minigalaxy.config import Config
            Config.first_run = True
            Config._Config__config = DEFAULT_CONFIGURATION
            lang = Config.get("lang")
        exp = "en"
        obs = lang
        self.assertEqual(exp, obs)

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.exists')
    def test_create_config(self, mock_exists, mock_isdir):
        mock_exists.side_effect = [False, True]
        mock_isdir.return_value = True
        with patch("builtins.open", mock_open()) as mock_config:
            from minigalaxy.config import Config
            Config.first_run = False
            Config.get("")
        mock_c = mock_config.mock_calls
        write_string = ""
        for kall in mock_c:
            name, args, kwargs = kall
            if name == "().write":
                write_string = "{}{}".format(write_string, args[0])
        exp = JSON_DEFAULT_CONFIGURATION
        obs = write_string
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    def test_set(self, mock_isfile):
        mock_isfile.return_value = True
        config = JSON_DEFAULT_CONFIGURATION
        with patch("builtins.open", mock_open(read_data=config)):
            from minigalaxy.config import Config
            Config.first_run = True
            Config.set("lang", "pl")
            lang = Config.get("lang")
        exp = "pl"
        obs = lang
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    def test_unset(self, mock_isfile):
        mock_isfile.return_value = True
        config = JSON_DEFAULT_CONFIGURATION
        with patch("builtins.open", mock_open(read_data=config)):
            from minigalaxy.config import Config
            Config.first_run = True
            Config.unset("lang")
            lang = Config.get("lang")
        exp = None
        obs = lang
        self.assertEqual(exp, obs)


del sys.modules['threading']
