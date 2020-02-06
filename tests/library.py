import unittest
from unittest.mock import MagicMock
from minigalaxy.ui.library import Library
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.game import Game

test_local_games = [
    Game("Leisure Suit Larry VGA", install_dir="/home/user/Games/Leisure Suit Larry VGA"),
    Game("Leisure Suit Larry", install_dir="/home/user/Games/Leisure Suit Larry"),
    Game("Leisure Suit Larry 3", install_dir="/home/user/Games/Leisure Suit Larry 3 - Passionate Patti in Pursuit of the Pulsating Pectorals!"),
    Game("Leisure Suit Larry 2", install_dir="/home/user/Games/Leisure Suit Larry 2 - Looking For Love (In Several Wrong Places)"),
    Game("Leisure Suit Larry 6 VGA", install_dir="/home/user/Games/Leisure Suit Larry 6 (VGA) - Shape Up Or Slip Out")
]

test_api_games = [
    Game("Leisure Suit Larry 1 - In the Land of the Lounge Lizards", game_id=1207662033),
    Game("Leisure Suit Larry 1 (VGA) - In the Land of the Lounge Lizards", game_id=1207662043),
    Game("Leisure Suit Larry 2 - Looking For Love (In Several Wrong Places)", game_id=1207662053),
    Game("Leisure Suit Larry 3 - Passionate Patti in Pursuit of the Pulsating Pectorals!", game_id=1207662063),
    Game("Leisure Suit Larry 5 - Passionate Patti Does a Little Undercover Work!", game_id=1207662073),
    Game("Leisure Suit Larry 6 - Shape Up Or Slip Out", game_id=1207662083),
    Game("Leisure Suit Larry 6 (VGA) - Shape Up Or Slip Out", game_id=1207662093),
    Game("Leisure Suit Larry: Love for Sail!", game_id=1207659174)
]


class LibraryTests(unittest.TestCase):
    config = Config()

    def test_no_games_before_update(self):
        library = Library(parent=None, api=Api(self.config), config=self.config)
        self.assertEqual(len(library.games), 0)

    def test_no_doubles_with_api(self):
        api = Api(self.config)
        library = Library(parent=None, api=api, config=self.config)
        api.get_library = MagicMock(return_value=test_api_games)
        library._Library__get_installed_games = MagicMock(return_value=test_local_games)
        library._Library__update_library()
        self.assertEqual(len(library.games), 8)


if __name__ == '__main__':
    unittest.main()
