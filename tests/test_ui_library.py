import sys
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch

from minigalaxy.game import Game

m_gtk = MagicMock()
m_window = MagicMock()
m_preferences = MagicMock()
m_gametile = MagicMock()
m_config = MagicMock()
sys.modules['gi.repository'] = m_gtk
sys.modules['minigalaxy.ui.window'] = m_window
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.gametile'] = m_gametile
sys.modules['minigalaxy.config'] = m_config

from minigalaxy.ui import library

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
    def test1_add_games_from_api(self):
        self_games = []
        for game in SELF_GAMES:
            self_games.append(Game(name=game, game_id=int(SELF_GAMES[game]),))
        api_games = []
        for game in API_GAMES:
            api_games.append(Game(name=game, game_id=int(API_GAMES[game]),))
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games
        test_library_games, offline = library.add_games_from_api(self_games, api_mock)
        exp = len(API_GAMES)
        obs = len(test_library_games)
        self.assertEqual(exp, obs)

    def test2_add_games_from_api(self):
        self_games = []
        for game in SELF_GAMES:
            self_games.append(Game(name=game, game_id=int(SELF_GAMES[game]),))
        api_games = []
        for game in API_GAMES:
            api_games.append(Game(name=game, game_id=int(API_GAMES[game]),))
        api_mock = MagicMock()
        api_mock.get_library.return_value = api_games
        test_library_games, offline = library.add_games_from_api(self_games, api_mock)
        exp = True
        obs = Game(name="Stellaris (English)", game_id=1508702879,) in test_library_games
        self.assertEqual(exp, obs)


del sys.modules['gi.repository']
del sys.modules['minigalaxy.ui.window']
del sys.modules['minigalaxy.ui.preferences']
del sys.modules['minigalaxy.ui.gametile']
del sys.modules['minigalaxy.config']