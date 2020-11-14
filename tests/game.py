import unittest
from unittest.mock import MagicMock
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

    def test1_validate_if_installed_is_latest(self):
        game = Game("Version Test game")
        game.installed_version = "gog-2"
        game.read_installed_version = MagicMock()
        installers = [{'id': 'installer_windows_en', 'name': 'Beneath a Steel Sky', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 91226112, 'files': [{'id': 'en1installer0', 'size': 91226112, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/en1installer0'}]}, {'id': 'installer_mac_en', 'name': 'Beneath a Steel Sky', 'os': 'mac', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 92274688, 'files': [{'id': 'en2installer0', 'size': 92274688, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/en2installer0'}]}, {'id': 'installer_linux_en', 'name': 'Beneath a Steel Sky', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 104857600, 'files': [{'id': 'en3installer0', 'size': 104857600, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/en3installer0'}]}, {'id': 'installer_windows_fr', 'name': 'Beneath a Steel Sky', 'os': 'windows', 'language': 'fr', 'language_full': 'français', 'version': '1.0', 'total_size': 91226112, 'files': [{'id': 'fr1installer2', 'size': 91226112, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/fr1installer2'}]}, {'id': 'installer_mac_fr', 'name': 'Beneath a Steel Sky', 'os': 'mac', 'language': 'fr', 'language_full': 'français', 'version': '1.0', 'total_size': 92274688, 'files': [{'id': 'fr2installer0', 'size': 92274688, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/fr2installer0'}]}, {'id': 'installer_linux_fr', 'name': 'Beneath a Steel Sky', 'os': 'linux', 'language': 'fr', 'language_full': 'français', 'version': 'gog-2', 'total_size': 104857600, 'files': [{'id': 'fr3installer2', 'size': 104857600, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/fr3installer2'}]}, {'id': 'installer_windows_it', 'name': 'Beneath a Steel Sky', 'os': 'windows', 'language': 'it', 'language_full': 'italiano', 'version': '1.0', 'total_size': 91226112, 'files': [{'id': 'it1installer2', 'size': 91226112, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/it1installer2'}]}, {'id': 'installer_mac_it', 'name': 'Beneath a Steel Sky', 'os': 'mac', 'language': 'it', 'language_full': 'italiano', 'version': '1.0', 'total_size': 92274688, 'files': [{'id': 'it2installer0', 'size': 92274688, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/it2installer0'}]}, {'id': 'installer_linux_it', 'name': 'Beneath a Steel Sky', 'os': 'linux', 'language': 'it', 'language_full': 'italiano', 'version': 'gog-2', 'total_size': 104857600, 'files': [{'id': 'it3installer2', 'size': 104857600, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/it3installer2'}]}, {'id': 'installer_windows_de', 'name': 'Beneath a Steel Sky', 'os': 'windows', 'language': 'de', 'language_full': 'Deutsch', 'version': '1.0', 'total_size': 91226112, 'files': [{'id': 'de1installer2', 'size': 91226112, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/de1installer2'}]}, {'id': 'installer_mac_de', 'name': 'Beneath a Steel Sky', 'os': 'mac', 'language': 'de', 'language_full': 'Deutsch', 'version': '1.0', 'total_size': 92274688, 'files': [{'id': 'de2installer0', 'size': 92274688, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/de2installer0'}]}, {'id': 'installer_linux_de', 'name': 'Beneath a Steel Sky', 'os': 'linux', 'language': 'de', 'language_full': 'Deutsch', 'version': 'gog-2', 'total_size': 104857600, 'files': [{'id': 'de3installer2', 'size': 104857600, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/de3installer2'}]}, {'id': 'installer_windows_es', 'name': 'Beneath a Steel Sky', 'os': 'windows', 'language': 'es', 'language_full': 'español', 'version': '1.0', 'total_size': 91226112, 'files': [{'id': 'es1installer2', 'size': 91226112, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/es1installer2'}]}, {'id': 'installer_mac_es', 'name': 'Beneath a Steel Sky', 'os': 'mac', 'language': 'es', 'language_full': 'español', 'version': '1.0', 'total_size': 92274688, 'files': [{'id': 'es2installer0', 'size': 92274688, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/es2installer0'}]}, {'id': 'installer_linux_es', 'name': 'Beneath a Steel Sky', 'os': 'linux', 'language': 'es', 'language_full': 'español', 'version': 'gog-2', 'total_size': 104857600, 'files': [{'id': 'es3installer2', 'size': 104857600, 'downlink': 'https://api.gog.com/products/1207658695/downlink/installer/es3installer2'}]}]
        expected = True
        observed = game.validate_if_installed_is_latest(installers)
        self.assertEqual(expected, observed)


if __name__ == '__main__':
    unittest.main()
