from unittest import TestCase, mock
from unittest.mock import MagicMock
import sys
import requests
import time
m_constants = MagicMock()
m_config = MagicMock()
sys.modules['minigalaxy.constants'] = m_constants
sys.modules['minigalaxy.config'] = m_config
from minigalaxy.api import Api

API_GET_INFO_TOONSTRUCK = {'downloads': {'installers': [{'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]},
                                    {'id': 'installer_mac_en', 'name': 'Toonstruck', 'os': 'mac', 'language': 'en', 'language_full': 'English', 'version': 'gog-3', 'total_size': 975175680, 'files': [{'id': 'en2installer0', 'size': 975175680, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en2installer0'}]},
                                    {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]},
                                    {'id': 'installer_windows_fr', 'name': 'Toonstruck', 'os': 'windows', 'language': 'fr', 'language_full': 'français', 'version': '1.0', 'total_size': 985661440, 'files': [{'id': 'fr1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer0'}, {'id': 'fr1installer1', 'size': 984612864, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer1'}]},
                                    {'id': 'installer_mac_fr', 'name': 'Toonstruck', 'os': 'mac', 'language': 'fr', 'language_full': 'français', 'version': 'gog-3', 'total_size': 1023410176, 'files': [{'id': 'fr2installer0', 'size': 1023410176, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr2installer0'}]},
                                    {'id': 'installer_linux_fr', 'name': 'Toonstruck', 'os': 'linux', 'language': 'fr', 'language_full': 'français', 'version': 'gog-2', 'total_size': 1011875840, 'files': [{'id': 'fr3installer0', 'size': 1011875840, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr3installer0'}]}]}}


class TestApi(TestCase):
    def test_get_login_url(self):
        api = Api()
        exp = "https://auth.gog.com/auth?client_id=46899977096215655&redirect_uri=https%3A%2F%2Fembed.gog.com%2Fon_login_success%3Forigin%3Dclient&response_type=code&layout=client2"
        obs = api.get_login_url()
        self.assertEqual(exp, obs)

    def test_get_redirect_url(self):
        api = Api()
        exp = "https://embed.gog.com/on_login_success?origin=client"
        obs = api.get_redirect_url()
        self.assertEqual(exp, obs)

    def test1_can_connect(self):
        api = Api()
        m_constants.return_value = True
        exp = True
        obs = api.can_connect()
        self.assertEqual(exp, obs)

    def test2_can_connect(self):
        api = Api()
        m_constants.SESSION.get.side_effect = requests.exceptions.ConnectionError(mock.Mock(status="Connection Error"))
        exp = False
        obs = api.can_connect()
        self.assertEqual(exp, obs)

    def test1_get_download_info(self):
        api = Api()
        api.get_info = MagicMock()
        api.get_info.return_value = API_GET_INFO_TOONSTRUCK
        m_config.Config.get.return_value = "pl"
        exp = {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]}
        obs = api.get_download_info("Test Game")
        self.assertEqual(exp, obs)

    def test2_get_download_info(self):
        api = Api()
        api.get_info = MagicMock()
        api.get_info.return_value = API_GET_INFO_TOONSTRUCK
        m_config.Config.get.return_value = "fr"
        exp = {'id': 'installer_linux_fr', 'name': 'Toonstruck', 'os': 'linux', 'language': 'fr', 'language_full': 'français', 'version': 'gog-2', 'total_size': 1011875840, 'files': [{'id': 'fr3installer0', 'size': 1011875840, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr3installer0'}]}
        obs = api.get_download_info("Test Game")
        self.assertEqual(exp, obs)
    
    def test3_get_download_info(self):
        api = Api()
        api.get_info = MagicMock()
        api.get_info.return_value = {'downloads': {'installers': [{'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]},
                                    {'id': 'installer_mac_en', 'name': 'Toonstruck', 'os': 'mac', 'language': 'en', 'language_full': 'English', 'version': 'gog-3', 'total_size': 975175680, 'files': [{'id': 'en2installer0', 'size': 975175680, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en2installer0'}]},
                                    {'id': 'installer_windows_fr', 'name': 'Toonstruck', 'os': 'windows', 'language': 'fr', 'language_full': 'français', 'version': '1.0', 'total_size': 985661440, 'files': [{'id': 'fr1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer0'}, {'id': 'fr1installer1', 'size': 984612864, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer1'}]},
                                    {'id': 'installer_mac_fr', 'name': 'Toonstruck', 'os': 'mac', 'language': 'fr', 'language_full': 'français', 'version': 'gog-3', 'total_size': 1023410176, 'files': [{'id': 'fr2installer0', 'size': 1023410176, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr2installer0'}]}]}}
        m_config.Config.get.return_value = "en"
        exp = {'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]}
        obs = api.get_download_info("Test Game")
        self.assertEqual(exp, obs)

    def test4_get_download_info(self):
        api = Api()
        dlc_test_installer = API_GET_INFO_TOONSTRUCK["downloads"]["installers"]
        m_config.Config.get.return_value = "en"
        exp = {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]}
        obs = api.get_download_info("Test Game", dlc_installers=dlc_test_installer)
        self.assertEqual(exp, obs)

    def test1_get_library(self):
        api = Api()
        api.active_token = "True"
        response_dict = {'totalPages': 1, 'products': [{'id': 1097893768, 'title': 'Neverwinter Nights: Enhanced Edition', 'image': '//images-2.gog-statics.com/8706f7fb87a4a41bc34254f3b49f59f96cf13d067b2c8bbfd8d41c327392052a', 'url': '/game/neverwinter_nights_enhanced_edition_pack', 'worksOn': {'Windows': True, 'Mac': True, 'Linux': True}}]}
        api.active_token_expiration_time = time.time() + 10.0
        response_mock = MagicMock()
        response_mock.json.return_value = response_dict
        m_constants.SESSION.get.return_value = response_mock
        exp = "Neverwinter Nights: Enhanced Edition"
        obs = api.get_library()[0].name
        self.assertEqual(exp, obs)

    def test1_get_version(self):
        api = Api()
        game = MagicMock()
        game.platform = "linux"
        exp = "gog-2"
        obs = api.get_version(game, gameinfo=API_GET_INFO_TOONSTRUCK)
        self.assertEqual(exp, obs)

    def test2_get_version(self):
        api = Api()
        game = MagicMock()
        game.platform = "linux"
        dlc_name = "Test DLC"
        game_info = API_GET_INFO_TOONSTRUCK
        game_info["expanded_dlcs"] = [{"title": dlc_name, "downloads": {"installers": [{"os": "linux", "version": "1.2.3.4"}]}}]
        exp = "1.2.3.4"
        obs = api.get_version(game, gameinfo=API_GET_INFO_TOONSTRUCK, dlc_name=dlc_name)
        self.assertEqual(exp, obs)

    def test_get_download_file_md5(self):
        api = Api()
        api._Api__request = MagicMock()
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="8acedf66c0d2986e7dee9af912b7df4f" chunks="4" timestamp="2015-07-30 17:11:12" total_size="36717998">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''
        exp = "8acedf66c0d2986e7dee9af912b7df4f"
        obs = api.get_download_file_md5("url")
        self.assertEqual(exp, obs)


del sys.modules['minigalaxy.constants']
del sys.modules['minigalaxy.config']
del sys.modules["minigalaxy.game"]
