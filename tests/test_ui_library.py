import json
import os
import sys
import uuid
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch, mock_open
import tempfile

m_gtk = MagicMock()
m_gi = MagicMock()
m_window = MagicMock()
m_preferences = MagicMock()
m_gametile = MagicMock()
m_gametilelist = MagicMock()
m_categoryfilters = MagicMock()


class UnitTestGtkTemplate:

    def __init__(self):
        self.Child = m_gtk

    def from_file(self, lib_file):
        def passthrough(func):
            def passthrough2(*args, **kwargs):
                return func(*args, **kwargs)
            return passthrough2
        return passthrough


class UnitTestGiRepository:

    class Gtk:

        Template = UnitTestGtkTemplate()
        Widget = m_gtk

        class Viewport:
            pass

    class Gdk:
        pass

    class GdkPixbuf:
        pass

    class Gio:
        pass

    class GLib:
        pass

    class Notify:
        pass


u_gi_repository = UnitTestGiRepository()
sys.modules['gi.repository'] = u_gi_repository
sys.modules['gi'] = m_gi
sys.modules['minigalaxy.ui.window'] = m_window
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.gametile'] = m_gametile
sys.modules['minigalaxy.ui.gametilelist'] = m_gametilelist
sys.modules['minigalaxy.ui.categoryfilters'] = m_categoryfilters
from minigalaxy.game import Game           # noqa: E402
from minigalaxy.ui.library import Library, get_installed_windows_games, read_game_categories_file, \
    update_game_categories_file  # noqa: E402

SELF_GAMES = {"Neverwinter Nights: Enhanced Edition": "1097893768", "Beneath A Steel Sky": "1207658695",
              "Stellaris (English)": "1508702879"}
API_GAMES = {"Neverwinter Nights: Enhanced Edition": "1097893768", "Beneath a Steel Sky": "1207658695",
             "Dragonsphere": "1207658927", "Warsow": "1207659121", "Outlast": "1207660064", "Xenonauts": "1207664803",
             "Wasteland 2": "1207665783", "Baldur's Gate: Enhanced Edition": "1207666353",
             "Baldur's Gate II: Enhanced Edition": "1207666373", "Toonstruck": "1207666633",
             "Icewind Dale: Enhanced Edition": "1207666683", "Pillars of Eternity": "1207666813",
             "Grim Fandango Remastered": "1207667183", "Knights of Pen and Paper +1 Edition": "1320675280",
             "Sunless Sea": "1421064427", "Dungeons 2": "1436885138", "Wasteland 2 Director's Cut": "1444386007",
             "Stellaris": "1508702879", "Butcher": "1689871374", "Reigns: Game of Thrones": "2060365190"}


class TestLibrary(TestCase):

    mock_config = MagicMock()
    mock_config.locale = "en"

    def test1_add_games_from_api(self):
        self_games = []
        for game in SELF_GAMES:
            self_games.append(Game(name=game, game_id=int(SELF_GAMES[game]),))
        api_games = []
        for game in API_GAMES:
            api_games.append(Game(name=game, game_id=int(API_GAMES[game]),))
        err_msg = ""
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games, err_msg
        test_library = Library(MagicMock(), self.mock_config, api_mock, MagicMock())
        test_library.games = self_games
        test_library._Library__add_games_from_api()
        exp = len(API_GAMES)
        obs = len(test_library.games)
        self.assertEqual(exp, obs)

    def test2_add_games_from_api(self):
        self_games = []
        for game in SELF_GAMES:
            self_games.append(Game(name=game, game_id=int(SELF_GAMES[game]),))
        api_games = []
        for game in API_GAMES:
            api_games.append(Game(name=game, game_id=int(API_GAMES[game]),))
        err_msg = ""
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games, err_msg
        test_library = Library(MagicMock(), self.mock_config, api_mock, MagicMock())
        test_library.games = self_games
        test_library._Library__add_games_from_api()
        exp = True
        obs = Game(name="Stellaris (English)", game_id=1508702879,) in test_library.games
        self.assertEqual(exp, obs)

    def test3_add_games_from_api(self):
        self_games = []
        for game in SELF_GAMES:
            self_games.append(Game(name=game, game_id=int(SELF_GAMES[game]),))
        self_games.append(Game(name="Game without ID", game_id=0))
        api_games = []
        for game in API_GAMES:
            api_games.append(Game(name=game, game_id=int(API_GAMES[game]),))
        api_gmae_with_id = Game(name="Game without ID", game_id=1234567890)
        api_games.append(api_gmae_with_id)
        err_msg = ""
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games, err_msg
        test_library = Library(MagicMock(), self.mock_config, api_mock, MagicMock())
        test_library.games = self_games
        test_library._Library__add_games_from_api()
        exp = True
        obs = api_gmae_with_id in test_library.games
        self.assertEqual(exp, obs)
        exp = len(api_games)
        obs = len(test_library.games)
        self.assertEqual(exp, obs)

    def test4_add_games_from_api(self):
        self_games = []
        for game in SELF_GAMES:
            self_games.append(Game(name=game, game_id=int(SELF_GAMES[game]),))
        api_games = []
        url_nr = 1
        for game in API_GAMES:
            api_games.append(Game(name=game, game_id=int(API_GAMES[game]), url="http://test_url{}".format(str(url_nr))))
            url_nr += 1
        err_msg = ""
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games, err_msg
        test_library = Library(MagicMock(), self.mock_config, api_mock, MagicMock())
        test_library.games = self_games
        test_library._Library__add_games_from_api()
        exp = "http://test_url1"
        obs = test_library.games[0].url
        self.assertEqual(exp, obs)

    def test5_add_games_from_api(self):
        self_games = []
        for game in SELF_GAMES:
            self_games.append(Game(name="{}_diff".format(game), game_id=int(SELF_GAMES[game]),))
        api_games = []
        for game in API_GAMES:
            api_games.append(Game(name=game, game_id=int(API_GAMES[game])))
        err_msg = ""
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games, err_msg
        test_library = Library(MagicMock(), self.mock_config, api_mock, MagicMock())
        test_library.games = self_games
        test_library._Library__add_games_from_api()
        exp = "Neverwinter Nights: Enhanced Edition"
        obs = test_library.games[0].name
        self.assertEqual(exp, obs)

    def test6_add_games_from_api(self):
        self_games = [Game(name="Torchlight 2", game_id=0, install_dir="/home/user/GoG Games/Torchlight II")]
        api_games = [Game(name="Torchlight II", game_id=1958228073)]
        err_msg = ""
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games, err_msg
        test_library = Library(MagicMock(), self.mock_config, api_mock, MagicMock())
        test_library.games = self_games
        test_library._Library__add_games_from_api()
        exp = 1
        obs = len(test_library.games)
        self.assertEqual(exp, obs)

    @mock.patch('os.listdir')
    def test1_get_installed_windows_game(self, mock_listdir):
        mock_listdir.return_value = ["goggame-1207665883.info"]
        # none-empty list of playTasks needed so that library recognizes it as installed game
        game_json_data = '{ "gameId": "1207665883", "name": "Aliens vs Predator Classic 2000", "playTasks":[{}]}'.encode('utf-8')
        with patch("builtins.open", mock_open(read_data=game_json_data)):
            games = get_installed_windows_games("/example/path")
        exp = "Aliens vs Predator Classic 2000"
        obs = games[0].name
        self.assertEqual(exp, obs)

    @mock.patch('os.listdir')
    def test2_get_installed_windows_game(self, mock_listdir):
        mock_listdir.return_value = ["goggame-1207665883.info"]
        # none-empty list of playTasks needed so that library recognizes it as installed game
        game_json_data = '{ "gameId": "1207665883", "name": "Aliens vs Predator Classic 2000", "playTasks":[{}]}'.encode('utf-8-sig')
        with patch("builtins.open", mock_open(read_data=game_json_data)):
            games = get_installed_windows_games("/example/path")
        exp = "Aliens vs Predator Classic 2000"
        obs = games[0].name
        self.assertEqual(exp, obs)

    def test_read_game_categories_file_should_return_populated_dict(self):
        with tempfile.NamedTemporaryFile(mode='w+t', delete=False) as tmpfile:
            tmpfile.write('{"Test Game":"Adventure"}')
            tmpfile.flush()

            actual = read_game_categories_file(tmpfile.name)

            self.assertTrue(len(actual))
            self.assertEqual(actual, {'Test Game': 'Adventure'})

    @mock.patch('os.path.exists')
    def test_update_game_categories_file_should_skip_for_empty_dict(self, mock_path_exists: MagicMock):
        mock_path_exists.side_effect = Exception("Test error")

        update_game_categories_file({}, None)

        self.assertFalse(mock_path_exists.called)

    def test_update_game_categories_file_should_create_file_if_not_found(self):
        initially_non_existent_file = f'/tmp/{uuid.uuid4()}.json'
        self.assertFalse(os.path.exists(initially_non_existent_file))
        expected = {'Test game': 'Adventure'}

        update_game_categories_file(expected, initially_non_existent_file)

        self.assertTrue(os.path.exists(initially_non_existent_file))
        self.assertDictEqual(expected, read_game_categories_file(initially_non_existent_file))

    def test_update_game_categories_file_should_skip_if_file_found_with_identical_contents(self):
        expected = {"Test Game": "Adventure"}
        with tempfile.NamedTemporaryFile(mode='r+t', delete=False) as tmpfile:
            json.dump(expected, tmpfile)
            tmpfile.flush()

            update_game_categories_file(expected, tmpfile.name)

            tmpfile.seek(os.SEEK_SET)
            actual = json.load(tmpfile)
            self.assertDictEqual(actual, expected)

    def test_update_game_categories_file_should_overwrite_file_if_contents_differ(self):
        with tempfile.NamedTemporaryFile(mode='w+t', delete=False) as tmpfile:
            tmpfile.write('{"Test Game":"Adventure"}')
            tmpfile.flush()
            expected = {"Test Game": "Adventure", "Another Game": "Strategy"}

            update_game_categories_file(expected, tmpfile.name)

            tmpfile.seek(os.SEEK_SET)
            actual = json.load(tmpfile)
            self.assertDictEqual(actual, expected)


del sys.modules['gi']
del sys.modules['gi.repository']
del sys.modules['minigalaxy.ui.window']
del sys.modules['minigalaxy.ui.preferences']
del sys.modules['minigalaxy.ui.gametile']
del sys.modules['minigalaxy.ui.gametilelist']
del sys.modules['minigalaxy.ui.categoryfilters']
