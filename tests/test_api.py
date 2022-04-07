import http
from unittest import TestCase, mock
from unittest.mock import MagicMock
import copy
import sys
import requests
import time
m_constants = MagicMock()
m_config = MagicMock()
sys.modules['minigalaxy.constants'] = m_constants
sys.modules['minigalaxy.config'] = m_config
from minigalaxy.api import Api    # noqa: E402
from minigalaxy.game import Game  # noqa: E402

API_GET_INFO_TOONSTRUCK = {'downloads': {'installers': [
    {'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]},
    {'id': 'installer_mac_en', 'name': 'Toonstruck', 'os': 'mac', 'language': 'en', 'language_full': 'English', 'version': 'gog-3', 'total_size': 975175680, 'files': [{'id': 'en2installer0', 'size': 975175680, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en2installer0'}]},
    {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]},
    {'id': 'installer_windows_fr', 'name': 'Toonstruck', 'os': 'windows', 'language': 'fr', 'language_full': 'français', 'version': '1.0', 'total_size': 985661440, 'files': [{'id': 'fr1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer0'}, {'id': 'fr1installer1', 'size': 984612864, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer1'}]},
    {'id': 'installer_mac_fr', 'name': 'Toonstruck', 'os': 'mac', 'language': 'fr', 'language_full': 'français', 'version': 'gog-3', 'total_size': 1023410176, 'files': [{'id': 'fr2installer0', 'size': 1023410176, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr2installer0'}]},
    {'id': 'installer_linux_fr', 'name': 'Toonstruck', 'os': 'linux', 'language': 'fr', 'language_full': 'français', 'version': 'gog-2', 'total_size': 1011875840, 'files': [{'id': 'fr3installer0', 'size': 1011875840, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr3installer0'}]}
]}}

API_GET_INFO_STELLARIS = [{'id': '51622789000874509', 'game_id': '51154268886064420', 'platform_id': 'gog', 'external_id': '1508702879', 'game': {'genres': [{'id': '51071904337940794', 'name': {'*': 'Strategy', 'en-US': 'Strategy'}, 'slug': 'strategy'}], 'summary': {'*': 'Stellaris description'}, 'visible_in_library': True, 'aggregated_rating': 78.5455, 'game_modes': [{'id': '53051895165351137', 'name': 'Single player', 'slug': 'single-player'}, {'id': '53051908711988230', 'name': 'Multiplayer', 'slug': 'multiplayer'}], 'horizontal_artwork': {'url_format': 'https://images.gog.com/742acfb77ec51ca48c9f96947bf1fc0ad8f0551c9c9f338021e8baa4f08e449f{formatter}.{ext}?namespace=gamesdb'}, 'background': {'url_format': 'https://images.gog.com/742acfb77ec51ca48c9f96947bf1fc0ad8f0551c9c9f338021e8baa4f08e449f{formatter}.{ext}?namespace=gamesdb'}, 'vertical_cover': {'url_format': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2{formatter}.{ext}?namespace=gamesdb'}, 'cover': {'url_format': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2{formatter}.{ext}?namespace=gamesdb'}, 'logo': {'url_format': 'https://images.gog.com/c50a5d26c42d84b4b884976fb89d10bb3e97ebda0c0450285d92b8c50844d788{formatter}.{ext}?namespace=gamesdb'}, 'icon': {'url_format': 'https://images.gog.com/c85cf82e6019dd52fcdf1c81d17687dd52807835f16aa938abd2a34e5d9b99d0{formatter}.{ext}?namespace=gamesdb'}, 'square_icon': {'url_format': 'https://images.gog.com/c3adc81bf37f1dd89c9da74c13967a08b9fd031af4331750dbc65ab0243493c8{formatter}.{ext}?namespace=gamesdb'}}}]
GAMESDB_INFO_STELLARIS = {'cover': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb', 'vertical_cover': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb', 'background': 'https://images.gog.com/742acfb77ec51ca48c9f96947bf1fc0ad8f0551c9c9f338021e8baa4f08e449f.png?namespace=gamesdb', 'summary': {'*': 'Stellaris description'}, 'genre': {'*': 'Strategy', 'en-US': 'Strategy'}}


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
        test_game = Game("Test Game")
        exp = {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]}
        obs = api.get_download_info(test_game)
        self.assertEqual(exp, obs)

    def test2_get_download_info(self):
        api = Api()
        api.get_info = MagicMock()
        api.get_info.return_value = API_GET_INFO_TOONSTRUCK
        m_config.Config.get.return_value = "fr"
        test_game = Game("Test Game")
        exp = {'id': 'installer_linux_fr', 'name': 'Toonstruck', 'os': 'linux', 'language': 'fr', 'language_full': 'français', 'version': 'gog-2', 'total_size': 1011875840, 'files': [{'id': 'fr3installer0', 'size': 1011875840, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr3installer0'}]}
        obs = api.get_download_info(test_game)
        self.assertEqual(exp, obs)

    def test3_get_download_info(self):
        api = Api()
        api.get_info = MagicMock()
        api.get_info.return_value = {'downloads': {'installers': [
            {'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]},
            {'id': 'installer_mac_en', 'name': 'Toonstruck', 'os': 'mac', 'language': 'en', 'language_full': 'English', 'version': 'gog-3', 'total_size': 975175680, 'files': [{'id': 'en2installer0', 'size': 975175680, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en2installer0'}]},
            {'id': 'installer_windows_fr', 'name': 'Toonstruck', 'os': 'windows', 'language': 'fr', 'language_full': 'français', 'version': '1.0', 'total_size': 985661440, 'files': [{'id': 'fr1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer0'}, {'id': 'fr1installer1', 'size': 984612864, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer1'}]},
            {'id': 'installer_mac_fr', 'name': 'Toonstruck', 'os': 'mac', 'language': 'fr', 'language_full': 'français', 'version': 'gog-3', 'total_size': 1023410176, 'files': [{'id': 'fr2installer0', 'size': 1023410176, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr2installer0'}]}
        ]}}
        m_config.Config.get.return_value = "en"
        test_game = Game("Test Game")
        exp = {'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]}
        obs = api.get_download_info(test_game)
        self.assertEqual(exp, obs)

    def test4_get_download_info(self):
        api = Api()
        dlc_test_installer = API_GET_INFO_TOONSTRUCK["downloads"]["installers"]
        m_config.Config.get.return_value = "en"
        test_game = Game("Test Game")
        exp = {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]}
        obs = api.get_download_info(test_game, dlc_installers=dlc_test_installer)
        self.assertEqual(exp, obs)

    def test1_get_library(self):
        api = Api()
        api.active_token = True
        response_dict = {'totalPages': 1, 'products': [{'id': 1097893768, 'title': 'Neverwinter Nights: Enhanced Edition', 'image': '//images-2.gog-statics.com/8706f7fb87a4a41bc34254f3b49f59f96cf13d067b2c8bbfd8d41c327392052a', 'url': '/game/neverwinter_nights_enhanced_edition_pack', 'worksOn': {'Windows': True, 'Mac': True, 'Linux': True}}]}
        api.active_token_expiration_time = time.time() + 10.0
        response_mock = MagicMock()
        response_mock.json.return_value = response_dict
        m_constants.SESSION.get.return_value = response_mock
        exp = "Neverwinter Nights: Enhanced Edition"
        retrieved_games, err_msg = api.get_library()
        obs = retrieved_games[0].name
        self.assertEqual(exp, obs)

    def test2_get_library(self):
        api = Api()
        api.active_token = False
        api.active_token_expiration_time = time.time() + 10.0
        response_mock = MagicMock()
        response_mock.json.return_value = {}
        m_constants.SESSION.get.return_value = response_mock
        exp = "Couldn't connect to GOG servers"
        retrieved_games, obs = api.get_library()
        self.assertEqual(exp, obs)

    def test1_get_version(self):
        api = Api()
        test_game = Game("Test Game", platform="linux")
        exp = "gog-2"
        obs = api.get_version(test_game, gameinfo=API_GET_INFO_TOONSTRUCK)
        self.assertEqual(exp, obs)

    def test2_get_version(self):
        api = Api()
        test_game = Game("Test Game", platform="linux")
        dlc_name = "Test DLC"
        game_info = API_GET_INFO_TOONSTRUCK
        game_info["expanded_dlcs"] = [{"title": dlc_name, "downloads": {"installers": [{"os": "linux", "version": "1.2.3.4"}]}}]
        exp = "1.2.3.4"
        obs = api.get_version(test_game, gameinfo=API_GET_INFO_TOONSTRUCK, dlc_name=dlc_name)
        self.assertEqual(exp, obs)

    def test_get_download_file_md5(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.OK
        m_constants.SESSION.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="8acedf66c0d2986e7dee9af912b7df4f" chunks="4" timestamp="2015-07-30 17:11:12" total_size="36717998">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''
        exp = "8acedf66c0d2986e7dee9af912b7df4f"
        obs = api.get_download_file_md5("url")
        self.assertEqual(exp, obs)

    def test_get_download_file_md5_returns_empty_string_on_empty_response(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.OK
        m_constants.SESSION.get().text = ""

        exp = ""
        obs = api.get_download_file_md5("url")
        self.assertEqual(exp, obs)

    def test_get_download_file_md5_returns_empty_string_on_response_error(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.NOT_FOUND

        exp = ""
        obs = api.get_download_file_md5("url")
        self.assertEqual(exp, obs)

    def test_get_download_file_md5_returns_empty_string_on_missing_md5(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.OK
        m_constants.SESSION.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="" chunks="4" timestamp="2015-07-30 17:11:12" total_size="36717998">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''

        exp = ""
        obs = api.get_download_file_md5("url")
        self.assertEqual(exp, obs)

    def test_get_file_size(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.OK
        m_constants.SESSION.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="8acedf66c0d2986e7dee9af912b7df4f" chunks="4" timestamp="2015-07-30 17:11:12" total_size="36717998">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''
        exp = 36717998
        obs = api.get_file_size("url")
        self.assertEqual(exp, obs)

    def test_get_file_size_returns_zero_on_empty_response(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.OK
        m_constants.SESSION.get().text = ""

        exp = 0
        obs = api.get_file_size("url")
        self.assertEqual(exp, obs)

    def test_get_file_size_returns_zero_on_response_error(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.NOT_FOUND

        exp = 0
        obs = api.get_file_size("url")
        self.assertEqual(exp, obs)

    def test_get_file_size_returns_zero_on_missing_total_size(self):
        api = Api()
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        m_constants.SESSION.get.side_effect = MagicMock()
        m_constants.SESSION.get().status_code = http.HTTPStatus.OK
        m_constants.SESSION.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="8acedf66c0d2986e7dee9af912b7df4f" chunks="4" timestamp="2015-07-30 17:11:12">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''

        exp = 0
        obs = api.get_file_size("url")
        self.assertEqual(exp, obs)

    def test1_get_gamesdb_info(self):
        api = Api()
        api._Api__request_gamesdb = MagicMock()
        api._Api__request_gamesdb.side_effect = [{}]
        test_game = Game("Test Game")
        exp = {"cover": "", "vertical_cover": "", "background": "", "genre": {}, "summary": {}}
        obs = api.get_gamesdb_info(test_game)
        self.assertEqual(exp, obs)

    def test2_get_gamesdb_info(self):
        api = Api()
        api._Api__request_gamesdb = MagicMock()
        api._Api__request_gamesdb.side_effect = API_GET_INFO_STELLARIS
        test_game = Game("Stellaris")
        exp = GAMESDB_INFO_STELLARIS
        obs = api.get_gamesdb_info(test_game)
        self.assertEqual(exp, obs)

    def test3_get_gamesdb_info_no_genre(self):
        api_info = copy.deepcopy(API_GET_INFO_STELLARIS)
        api_info[0]["game"]["genres"] = []
        api_info[0]["game"]["genres_ids"] = []
        api = Api()
        api._Api__request_gamesdb = MagicMock()
        api._Api__request_gamesdb.side_effect = api_info

        test_game = Game("Stellaris")
        exp = copy.deepcopy(GAMESDB_INFO_STELLARIS)
        exp['genre'] = {}
        obs = api.get_gamesdb_info(test_game)
        self.assertEqual(exp, obs)


del sys.modules['minigalaxy.constants']
del sys.modules['minigalaxy.config']
del sys.modules["minigalaxy.game"]
