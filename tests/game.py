import unittest
from minigalaxy.game import Game


class MyTestCase(unittest.TestCase):
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
        larry1_local_gog = Game("Leisure Suit Larry", install_dir="/home/user/Games/Leisure Suit Larry", game_id=1207662033)
        larry1_local_minigalaxy = Game("Leisure Suit Larry", install_dir="/home/wouter/Games/Leisure Suit Larry 1 - In the Land of the Lounge Lizards", game_id=1207662033)

        self.assertEqual(larry1_local_gog, larry1_local_minigalaxy)
        self.assertEqual(larry1_local_minigalaxy, larry1_api)
        self.assertEqual(larry1_local_gog, larry1_api)

        larry2_api = Game("Leisure Suit Larry 2 - Looking For Love (In Several Wrong Places)", game_id=1207662053)
        larry2_local_minigalaxy = Game("Leisure Suit Larry 2", install_dir="/home/user/Games/Leisure Suit Larry 2 - Looking For Love (In Several Wrong Places)", game_id=1207662053)
        larry2_local_gog = Game("Leisure Suit Larry 2", install_dir="/home/user/Games/Leisure Suit Larry 2", game_id=1207662053)

        self.assertNotEqual(larry1_api, larry2_api)
        self.assertNotEqual(larry2_local_gog, larry1_api)
        self.assertNotEqual(larry2_local_gog, larry1_local_gog)
        self.assertNotEqual(larry2_local_gog, larry1_local_minigalaxy)
        self.assertNotEqual(larry2_local_minigalaxy, larry1_api)
        self.assertNotEqual(larry2_local_minigalaxy, larry1_local_minigalaxy)

    def test_local_comparison(self):
        larry1_local_gog = Game("Leisure Suit Larry", install_dir="/home/user/Games/Leisure Suit Larry", game_id=1207662033)
        larry1_vga_local_gog = Game("Leisure Suit Larry VGA", install_dir="/home/user/Games/Leisure Suit Larry VGA", game_id=1207662043)

        self.assertNotEqual(larry1_local_gog, larry1_vga_local_gog)


if __name__ == '__main__':
    unittest.main()
