import unittest
import sys
import os
from unittest.mock import MagicMock, mock_open, patch

m_config = MagicMock()
m_paths = MagicMock()
sys.modules['minigalaxy.config'] = m_config
sys.modules['minigalaxy.paths'] = m_paths
m_paths.CONFIG_GAMES_DIR = "/home/user/.config/minigalaxy/games/"
from minigalaxy.game import Game  # noqa: E402


class TestGame(unittest.TestCase):
    def test_strip_within_comparison(self):
        game1 = Game("!@#$%^&*(){}[]\"'_-<>.,;:")
        game2 = Game("")
        game3 = Game("hallo")
        game4 = Game("Hallo")
        game5 = Game("Hallo!")
        self.assertEqual(game1, game2)
        self.assertNotEqual(game2, game3)
        self.assertEqual(game3, game4)
        self.assertEqual(game3, game5)

    def test_local_and_api_comparison(self):
        larry1_api = Game("Leisure Suit Larry 1 - In the Land of the Lounge Lizards", game_id=1207662033)
        larry1_local_gog = Game("Leisure Suit Larry", install_dir="/home/user/Games/Leisure Suit Larry",
                                game_id=1207662033)
        larry1_local_minigalaxy = Game("Leisure Suit Larry",
                                       install_dir="/home/wouter/Games/Leisure Suit Larry 1 - In the Land of the Lounge Lizards",
                                       game_id=1207662033)

        self.assertEqual(larry1_local_gog, larry1_local_minigalaxy)
        self.assertEqual(larry1_local_minigalaxy, larry1_api)
        self.assertEqual(larry1_local_gog, larry1_api)

        larry2_api = Game("Leisure Suit Larry 2 - Looking For Love (In Several Wrong Places)", game_id=1207662053)
        larry2_local_minigalaxy = Game("Leisure Suit Larry 2",
                                       install_dir="/home/user/Games/Leisure Suit Larry 2 - Looking For Love (In Several Wrong Places)",
                                       game_id=1207662053)
        larry2_local_gog = Game("Leisure Suit Larry 2", install_dir="/home/user/Games/Leisure Suit Larry 2",
                                game_id=1207662053)

        self.assertNotEqual(larry1_api, larry2_api)
        self.assertNotEqual(larry2_local_gog, larry1_api)
        self.assertNotEqual(larry2_local_gog, larry1_local_gog)
        self.assertNotEqual(larry2_local_gog, larry1_local_minigalaxy)
        self.assertNotEqual(larry2_local_minigalaxy, larry1_api)
        self.assertNotEqual(larry2_local_minigalaxy, larry1_local_minigalaxy)

    def test_local_comparison(self):
        larry1_local_gog = Game("Leisure Suit Larry", install_dir="/home/user/Games/Leisure Suit Larry",
                                game_id=1207662033)
        larry1_vga_local_gog = Game("Leisure Suit Larry VGA", install_dir="/home/user/Games/Leisure Suit Larry VGA",
                                    game_id=1207662043)

        self.assertNotEqual(larry1_local_gog, larry1_vga_local_gog)

    def test1_is_update_available(self):
        game = Game("Version Test game")
        game.load_minigalaxy_info_json = MagicMock()
        game.load_minigalaxy_info_json.return_value = {'version': 'gog-2'}
        expected = True
        observed = game.is_update_available("gog-3")
        self.assertEqual(expected, observed)

    def test2_is_update_available(self):
        game = Game("Version Test game")
        game.load_minigalaxy_info_json = MagicMock()
        game.load_minigalaxy_info_json.return_value = {'version': "91.8193.16"}
        expected = False
        observed = game.is_update_available("91.8193.16")
        self.assertEqual(expected, observed)

    def test3_is_update_available(self):
        game = Game("Version Test game")
        game.load_minigalaxy_info_json = MagicMock()
        game.load_minigalaxy_info_json.return_value = {'version': "91.8193.16", "dlcs": {"Neverwinter Nights: Wyvern Crown of Cormyr": {"version": "82.8193.20.1"}}}
        expected = True
        observed = game.is_update_available("91.8193.16", dlc_title="Neverwinter Nights: Wyvern Crown of Cormyr")
        self.assertEqual(expected, observed)

    def test4_is_update_available(self):
        game = Game("Version Test game")
        game.load_minigalaxy_info_json = MagicMock()
        game.load_minigalaxy_info_json.return_value = {'version': "91.8193.16", "dlcs": {"Neverwinter Nights: Wyvern Crown of Cormyr": {"version": "82.8193.20.1"}}}
        expected = False
        observed = game.is_update_available("82.8193.20.1", dlc_title="Neverwinter Nights: Wyvern Crown of Cormyr")
        self.assertEqual(expected, observed)

    def test1_get_install_directory_name(self):
        game = Game("Get Install Directory Test1")
        expected = "Get Install Directory Test1"
        observed = game.get_install_directory_name()
        self.assertEqual(expected, observed)

    def test2_get_install_directory_name(self):
        game = Game("Get\r Install\n Directory Test2!@#$%")
        expected = "Get Install Directory Test2"
        observed = game.get_install_directory_name()
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test1_fallback_read_installed_version(self, mock_isfile):
        mock_isfile.return_value = True
        gameinfo = """Beneath A Steel Sky
gog-2
20150
en-US
1207658695
1207658695
664777434"""
        game = Game("Game Name test1")
        expected = "gog-2"
        with patch("builtins.open", mock_open(read_data=gameinfo)):
            observed = game.fallback_read_installed_version()
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test2_fallback_read_installed_version(self, mock_isfile):
        mock_isfile.return_value = False
        gameinfo = """Beneath A Steel Sky
    gog-2
    20150
    en-US
    1207658695
    1207658695
    664777434"""
        game = Game("Game Name test2")
        expected = "0"
        with patch("builtins.open", mock_open(read_data=gameinfo)):
            observed = game.fallback_read_installed_version()
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.exists')
    def test1_set_info(self, mock_exists):
        mock_exists.return_value = True
        json_content = '{"version": "gog-2"}'
        with patch("builtins.open", mock_open(read_data=json_content)) as m:
            game = Game("Game Name test2")
            game.set_info("version", "gog-3")
        mock_c = m.mock_calls
        write_string = ""
        for kall in mock_c:
            name, args, kwargs = kall
            if name == "().write":
                write_string = "{}{}".format(write_string, args[0])
        expected = '{"version": "gog-3"}'
        observed = write_string
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.exists')
    @unittest.mock.patch('os.makedirs')
    def test2_set_dlc_info(self, mock_makedirs, mock_exists):
        mock_exists.return_value = False
        dlc_name = "Neverwinter Nights: Wyvern Crown of Cormyr"
        with patch("builtins.open", mock_open()) as m:
            game = Game("Neverwinter Nights")
            game.set_dlc_info("version", "82.8193.20.1", dlc_name)
        mock_c = m.mock_calls
        write_string = ""
        for kall in mock_c:
            name, args, kwargs = kall
            if name == "().write":
                write_string = "{}{}".format(write_string, args[0])
        expected = '{"dlcs": {"Neverwinter Nights: Wyvern Crown of Cormyr": {"version": "82.8193.20.1"}}}'
        observed = write_string
        self.assertEqual(expected, observed)

    def test_get_stripped_name(self):
        name_string = "Beneath A Steel Sky"
        game = Game(name_string)
        expected = "BeneathASteelSky"
        observed = game.get_stripped_name()
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test1_load_minigalaxy_info_json(self, mock_isfile):
        mock_isfile.side_effect = [True]
        json_content = '{"version": "gog-2"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test2")
            jscon_dict = game.load_minigalaxy_info_json()
        expected = {"version": "gog-2"}
        observed = jscon_dict
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test2_load_minigalaxy_info_json(self, mock_isfile):
        mock_isfile.side_effect = [False]
        json_content = '{"version": "gog-2"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test2")
            jscon_dict = game.load_minigalaxy_info_json()
        expected = {}
        observed = jscon_dict
        self.assertEqual(expected, observed)

    @unittest.mock.patch("minigalaxy.config.Config")
    @unittest.mock.patch('os.makedirs')
    def test_save_minigalaxy_info_json(self, mock_makedirs, mock_config):
        json_dict = {"version": "gog-2"}
        with patch("builtins.open", mock_open()) as m:
            game = Game("Neverwinter Nights")
            game.save_minigalaxy_info_json(json_dict)
        mock_c = m.mock_calls
        write_string = ""
        for kall in mock_c:
            name, args, kwargs = kall
            if name == "().write":
                write_string = "{}{}".format(write_string, args[0])
        expected = '{"version": "gog-2"}'
        observed = write_string
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.exists')
    def test1_is_installed(self, mock_isfile):
        mock_isfile.side_effect = [False]
        game = Game("Game Name Test")
        game.load_minigalaxy_info_json = MagicMock()
        exp = False
        obs = game.is_installed()
        self.assertEqual(exp, obs)

    @unittest.mock.patch('os.path.exists')
    def test2_is_installed(self, mock_isfile):
        mock_isfile.side_effect = [True]
        game = Game("Game Name Test", install_dir="Test Install Dir")
        game.load_minigalaxy_info_json = MagicMock()
        game.load_minigalaxy_info_json.return_value = {"dlcs": {"Neverwinter Nights: Wyvern Crown of Cormyr": {"version": "82.8193.20.1"}}}
        exp = True
        obs = game.is_installed(dlc_title="Neverwinter Nights: Wyvern Crown of Cormyr")
        self.assertEqual(exp, obs)

    @unittest.mock.patch('os.path.exists')
    def test3_is_installed(self, mock_isfile):
        mock_isfile.side_effect = [True]
        game = Game("Game Name Test", install_dir="Test Install Dir")
        game.load_minigalaxy_info_json = MagicMock()
        game.load_minigalaxy_info_json.return_value = {"dlcs": {"Neverwinter Nights: Wyvern Crown of Cormyr": {"version": "82.8193.20.1"}}}
        game.legacy_get_dlc_status = MagicMock()
        game.legacy_get_dlc_status.return_value = "not-installed"
        exp = False
        obs = game.is_installed(dlc_title="Not Present DLC")
        self.assertEqual(exp, obs)

    @unittest.mock.patch('os.path.isfile')
    def test_get_info(self, mock_isfile):
        mock_isfile.side_effect = [True]
        json_content = '{"example_key": "example_value"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game_get_status = game.get_info("example_key")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test_get_dlc_info(self, mock_isfile):
        mock_isfile.side_effect = [True, False]
        json_content = '{"dlcs": {"example_dlc" : {"example_key": "example_value"}}}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game_get_status = game.get_dlc_info("example_key", "example_dlc")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    def test_set_install_dir(self):
        install_directory = "/home/user/GOG Games"
        install_game_name = "Neverwinter Nights"
        m_config.Config.get.return_value = install_directory
        game = Game(install_game_name)
        game.set_install_dir()
        exp = os.path.join(install_directory, install_game_name)
        obs = game.install_dir
        self.assertEqual(exp, obs)

    @unittest.mock.patch('os.path.isfile')
    def test1_get_info_legacy(self, mock_isfile):
        mock_isfile.side_effect = [False, True]
        json_content = '{"example_key": "example_value"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game.set_info = MagicMock()
            game_get_status = game.get_info("example_key")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test2_get_info_legacy(self, mock_isfile):
        mock_isfile.side_effect = [True, True]
        json_content = '{"example_key": "example_value"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game.set_info = MagicMock()
            game.load_minigalaxy_info_json = MagicMock()
            game.load_minigalaxy_info_json.return_value = {}
            game_get_status = game.get_info("example_key")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test3_get_info_legacy(self, mock_isfile):
        mock_isfile.side_effect = [True, True]
        json_content = '{"example_key": "example_value_legacy"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game.load_minigalaxy_info_json = MagicMock()
            game.load_minigalaxy_info_json.return_value = {"example_key": "example_value"}
            game_get_status = game.get_info("example_key")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test1_get_dlc_info_legacy(self, mock_isfile):
        mock_isfile.side_effect = [False, True]
        json_content = '{"dlcs": {"example_dlc" : {"example_key": "example_value"}}}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game.set_dlc_info = MagicMock()
            game_get_status = game.get_dlc_info("example_key", "example_dlc")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test2_get_dlc_info_legacy(self, mock_isfile):
        mock_isfile.side_effect = [True, True]
        json_content = '{"dlcs": {"example_dlc" : {"example_key": "example_value"}}}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game.set_dlc_info = MagicMock()
            game.load_minigalaxy_info_json = MagicMock()
            game.load_minigalaxy_info_json.return_value = {}
            game_get_status = game.get_dlc_info("example_key", "example_dlc")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    @unittest.mock.patch('os.path.isfile')
    def test3_get_dlc_info_legacy(self, mock_isfile):
        mock_isfile.side_effect = [True, True]
        json_content = '{"dlcs": {"example_dlc" : {"example_key": "example_value_legacy"}}}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            game = Game("Game Name test")
            game.load_minigalaxy_info_json = MagicMock()
            game.load_minigalaxy_info_json.return_value = {"dlcs": {"example_dlc": {"example_key": "example_value"}}}
            game_get_status = game.get_dlc_info("example_key", "example_dlc")
        expected = "example_value"
        observed = game_get_status
        self.assertEqual(expected, observed)

    def test1_get_status_file_path(self):
        game = Game(name="Europa Universalis 2")
        expected = "/home/user/.config/minigalaxy/games/Europa Universalis 2.json"
        observed = game.get_status_file_path()
        self.assertEqual(expected, observed)

    def test2_get_status_file_path(self):
        game = Game(name="Europa Universalis 2", install_dir="/home/user/GoG Games//Europa Universalis II")
        expected = "/home/user/.config/minigalaxy/games/Europa Universalis II.json"
        observed = game.get_status_file_path()
        self.assertEqual(expected, observed)


del sys.modules["minigalaxy.config"]
del sys.modules["minigalaxy.paths"]
