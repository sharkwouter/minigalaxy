import json
import os
import sys
import uuid
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch, mock_open
import tempfile
from tests.ui import MockGiRepository

m_gtk = MagicMock()
m_gi = MagicMock()
m_window = MagicMock()
m_preferences = MagicMock()
m_gametile = MagicMock()
m_gametilelist = MagicMock()
m_categoryfilters = MagicMock()

sys.modules['gi.repository'] = MockGiRepository()
sys.modules['gi'] = m_gi
sys.modules['minigalaxy.ui.window'] = m_window
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.gametile'] = m_gametile
sys.modules['minigalaxy.ui.gametilelist'] = m_gametilelist
sys.modules['minigalaxy.ui.categoryfilters'] = m_categoryfilters
from minigalaxy.game import Game           # noqa: E402
from minigalaxy.ui.gametile import GameTile  # noqa: E402
from minigalaxy.ui import library as library_module  # noqa: E402
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

    def test_installed_games_removed_from_current_downloads(self):
        """Make sure that library detects when already installed games are still marked as to be downloaded"""

        # none-empty list of playTasks needed so that library recognizes it as installed game
        game_json_data = '{ "gameId": "1207665883", "name": "Aliens vs Predator Classic 2000", "playTasks":[{}]}'
        gog_info_file = "goggame-1207665883.info"
        self.mock_config.current_downloads = [1207665883]
        self.mock_config.remove_ongoing_download.side_effect = lambda gameid: self.mock_config.current_downloads.remove(gameid)

        api_mock = MagicMock()
        test_library = Library(MagicMock(), self.mock_config, api_mock, MagicMock())

        with tempfile.TemporaryDirectory() as tmpdir:
            self.mock_config.install_dir = tmpdir
            os.makedirs(f'{tmpdir}/Alien', mode=0o755)
            with open(f'{tmpdir}/Alien/{gog_info_file}', "w", encoding="utf-8") as file:
                file.write(game_json_data)
            test_library._Library__get_installed_games()

        self.mock_config.remove_ongoing_download.assert_called_once()
        self.assertEqual([], self.mock_config.current_downloads)
        self.mock_config.save.assert_called_once()

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

    def _tile_library(self, installed, api_games, err_msg=""):
        config = MagicMock()
        config.locale = "en"
        config.installed_filter = False
        config.platform_mode = ["linux"]
        config.view = "grid"
        config.current_downloads = []
        config.show_hidden_games = True
        api = MagicMock()
        api.get_owned_products_ids.return_value = []
        api.get_library.return_value = api_games, err_msg
        library = Library(MagicMock(), config, api, MagicMock())
        library.flowbox.get_children.return_value = []
        library._Library__get_installed_games = MagicMock(return_value=installed)
        GameTile.reset_mock()
        library.flowbox.reset_mock()
        library.flowbox.get_children.return_value = []
        return library

    def _flush_idle(self, queue, count=1):
        for _ in range(count):
            func, args = queue.pop(0)
            func(*args)

    def _flush_all_idle(self, queue):
        while queue:
            self._flush_idle(queue, 1)

    def _added_tile_games(self):
        return [call.args[1] for call in GameTile.call_args_list]

    def _mixed_library_games(self, tmpdir):
        """Installed linux + windows-only rows mixed with not-installed linux titles.

        Interleaving hidden-platform rows with shown ones is the shape that
        skipped later linux titles when tiles were created in index chunks
        while Windows rows were removed from the live list.
        """
        installed = Game(name="Installed Linux", game_id=1, install_dir=tmpdir, platform="linux")
        linux_games = [
            Game(name=f"Linux Game {i}", game_id=100 + i, platform="linux")
            for i in range(4)
        ]
        windows = [
            Game(name=f"Windows Only {i}", game_id=9000 + i, platform="windows")
            for i in range(8)
        ]
        api_games = [
            Game(name="Installed Linux", game_id=1, platform="linux"),
            windows[0], windows[1], windows[2], windows[3],
            linux_games[0],
            windows[4],
            linux_games[1],
            windows[5],
            linux_games[2],
            windows[6], windows[7],
            linux_games[3],
        ]
        return [installed], api_games, linux_games, windows

    def test_update_library_does_not_skip_not_installed_linux_games(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            installed, api_games, expected_linux, _windows = self._mixed_library_games(tmpdir)
            library = self._tile_library(installed, api_games)
            library._library_generation = 1
            library._Library__update_library(1)

            added_ids = {game.id for game in self._added_tile_games()}
            self.assertIn(installed[0].id, added_ids)
            for game in expected_linux:
                self.assertIn(game.id, added_ids, f"{game.name} should have a tile")

    def test_update_library_removes_windows_only_games(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            installed, api_games, expected_linux, windows = self._mixed_library_games(tmpdir)
            library = self._tile_library(installed, api_games)
            library._library_generation = 1
            library._Library__update_library(1)

            remaining_ids = {game.id for game in library.games}
            added_ids = {game.id for game in self._added_tile_games()}
            for game in windows:
                self.assertNotIn(game.id, remaining_ids)
                self.assertNotIn(game.id, added_ids)
            for game in expected_linux:
                self.assertIn(game.id, remaining_ids)

    def test_update_library_keeps_installed_windows_games(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            installed_windows = Game(
                name="Installed Windows", game_id=42, install_dir=tmpdir, platform="windows"
            )
            api_windows = Game(name="Installed Windows", game_id=42, platform="windows")
            downloadable_windows = Game(name="Uninstalled Windows", game_id=43, platform="windows")
            library = self._tile_library([installed_windows], [api_windows, downloadable_windows])
            library._library_generation = 1
            library._Library__update_library(1)

            remaining_ids = {game.id for game in library.games}
            added_ids = {game.id for game in self._added_tile_games()}
            self.assertIn(42, remaining_ids)
            self.assertIn(42, added_ids)
            self.assertNotIn(43, remaining_ids)
            self.assertNotIn(43, added_ids)

    def test_update_library_applies_installed_before_api(self):
        idle_queue = []
        events = []

        def queue_idle(func, *args):
            events.append(func)
            idle_queue.append((func, args))
            return 0

        with tempfile.TemporaryDirectory() as tmpdir:
            installed, api_games, expected_linux, windows = self._mixed_library_games(tmpdir)
            library = self._tile_library(installed, api_games)
            library.api.get_library.side_effect = lambda: (events.append("api"), (api_games, ""))[1]
            library._library_generation = 1
            apply_installed = library._Library__apply_installed_games
            with patch.object(library_module.GLib, "idle_add", side_effect=queue_idle):
                library._Library__update_library(1)

                self.assertIn("api", events)
                self.assertLess(events.index(apply_installed), events.index("api"))

                self._flush_idle(idle_queue, 1)
                self.assertEqual([], self._added_tile_games())

                self._flush_idle(idle_queue, 1)
                added_after_installed = self._added_tile_games()
                self.assertEqual([installed[0].id], [game.id for game in added_after_installed])
                for game in expected_linux:
                    self.assertNotIn(game.id, {g.id for g in added_after_installed})

                self._flush_idle(idle_queue, 1)
                self._flush_all_idle(idle_queue)
                added_after_api = self._added_tile_games()
                added_ids = {game.id for game in added_after_api}
                self.assertEqual(1 + len(expected_linux), len(added_after_api))
                for game in expected_linux:
                    self.assertIn(game.id, added_ids)
                for game in windows:
                    self.assertNotIn(game.id, added_ids)
                self.assertEqual([], idle_queue)

    def test_update_library_sets_filter_before_adding_tiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            installed, api_games, _linux, _windows = self._mixed_library_games(tmpdir)
            library = self._tile_library(installed, api_games)
            library._library_generation = 1
            library._Library__update_library(1)

            method_names = [name for name, _args, _kwargs in library.flowbox.mock_calls]
            self.assertIn("set_filter_func", method_names)
            self.assertIn("add", method_names)
            self.assertLess(method_names.index("set_filter_func"), method_names.index("add"))

    def test_stale_generation_apply_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            installed, api_games, expected_linux, _windows = self._mixed_library_games(tmpdir)
            library = self._tile_library(installed, api_games)
            library._library_generation = 2
            library._Library__apply_installed_games(installed, 1)
            library._Library__apply_api_games(api_games, "", 1)

            self.assertEqual([], library.games)
            self.assertEqual([], self._added_tile_games())
            for game in expected_linux:
                self.assertIsNone(game.library_tile)


del sys.modules['gi']
del sys.modules['gi.repository']
del sys.modules['minigalaxy.ui.window']
del sys.modules['minigalaxy.ui.preferences']
del sys.modules['minigalaxy.ui.gametile']
del sys.modules['minigalaxy.ui.gametilelist']
del sys.modules['minigalaxy.ui.categoryfilters']
