import datetime
import http
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch
import copy
import requests
import time
from minigalaxy.api import Api
from minigalaxy.entity.download_info import DownloadInfo
from minigalaxy.entity.download_chunk import DownloadChunk
from minigalaxy.entity.xml_exception import XmlException
from minigalaxy.game import Game

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
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        exp = "https://auth.gog.com/auth?client_id=46899977096215655&redirect_uri=https%3A%2F%2Fembed.gog.com%2Fon_login_success%3Forigin%3Dclient&response_type=code&layout=client2"
        obs = api.get_login_url()
        self.assertEqual(exp, obs)

    def test_get_redirect_url(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        exp = "https://embed.gog.com/on_login_success?origin=client"
        obs = api.get_redirect_url()
        self.assertEqual(exp, obs)

    def test1_can_connect(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        exp = True
        obs = api.can_connect()
        self.assertEqual(exp, obs)

    def test2_can_connect(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        session.get.side_effect = requests.exceptions.ConnectionError(Mock(status="Connection Error"))
        exp = False
        obs = api.can_connect()
        self.assertEqual(exp, obs)

    def test1_get_download_info(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api.get_info = MagicMock()
        api.get_info.return_value = API_GET_INFO_TOONSTRUCK
        config.lang = "pl"
        test_game = Game("Test Game")
        exp = {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]}
        obs = api.get_download_info(test_game)
        self.assertEqual(exp, obs)

    def test2_get_download_info(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api.get_info = MagicMock()
        api.get_info.return_value = API_GET_INFO_TOONSTRUCK
        config.lang = "fr"
        test_game = Game("Test Game")
        exp = {'id': 'installer_linux_fr', 'name': 'Toonstruck', 'os': 'linux', 'language': 'fr', 'language_full': 'français', 'version': 'gog-2', 'total_size': 1011875840, 'files': [{'id': 'fr3installer0', 'size': 1011875840, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr3installer0'}]}
        obs = api.get_download_info(test_game)
        self.assertEqual(exp, obs)

    def test3_get_download_info(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api.get_info = MagicMock()
        api.get_info.return_value = {'downloads': {'installers': [
            {'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]},
            {'id': 'installer_mac_en', 'name': 'Toonstruck', 'os': 'mac', 'language': 'en', 'language_full': 'English', 'version': 'gog-3', 'total_size': 975175680, 'files': [{'id': 'en2installer0', 'size': 975175680, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en2installer0'}]},
            {'id': 'installer_windows_fr', 'name': 'Toonstruck', 'os': 'windows', 'language': 'fr', 'language_full': 'français', 'version': '1.0', 'total_size': 985661440, 'files': [{'id': 'fr1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer0'}, {'id': 'fr1installer1', 'size': 984612864, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr1installer1'}]},
            {'id': 'installer_mac_fr', 'name': 'Toonstruck', 'os': 'mac', 'language': 'fr', 'language_full': 'français', 'version': 'gog-3', 'total_size': 1023410176, 'files': [{'id': 'fr2installer0', 'size': 1023410176, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/fr2installer0'}]}
        ]}}
        config.lang = "en"
        test_game = Game("Test Game")
        exp = {'id': 'installer_windows_en', 'name': 'Toonstruck', 'os': 'windows', 'language': 'en', 'language_full': 'English', 'version': '1.0', 'total_size': 939524096, 'files': [{'id': 'en1installer0', 'size': 1048576, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer0'}, {'id': 'en1installer1', 'size': 938475520, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en1installer1'}]}
        obs = api.get_download_info(test_game)
        self.assertEqual(exp, obs)

    def test4_get_download_info(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        dlc_test_installer = API_GET_INFO_TOONSTRUCK["downloads"]["installers"]
        config.lang = "en"
        test_game = Game("Test Game")
        exp = {'id': 'installer_linux_en', 'name': 'Toonstruck', 'os': 'linux', 'language': 'en', 'language_full': 'English', 'version': 'gog-2', 'total_size': 963641344, 'files': [{'id': 'en3installer0', 'size': 963641344, 'downlink': 'https://api.gog.com/products/1207666633/downlink/installer/en3installer0'}]}
        obs = api.get_download_info(test_game, dlc_installers=dlc_test_installer)
        self.assertEqual(exp, obs)

    def test1_get_library(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api.active_token = True
        response_dict = {'totalPages': 1, 'products': [{'id': 1097893768, 'title': 'Neverwinter Nights: Enhanced Edition', 'image': '//images-2.gog-statics.com/8706f7fb87a4a41bc34254f3b49f59f96cf13d067b2c8bbfd8d41c327392052a', 'url': '/game/neverwinter_nights_enhanced_edition_pack', 'worksOn': {'Windows': True, 'Mac': True, 'Linux': True}}]}
        api.active_token_expiration_time = time.time() + 10.0
        response_mock = MagicMock()
        response_mock.json.return_value = response_dict
        session.get.return_value = response_mock
        session.get().status_code = http.HTTPStatus.OK
        exp = "Neverwinter Nights: Enhanced Edition"
        retrieved_games, err_msg = api.get_library()
        obs = retrieved_games[0].name
        self.assertEqual(exp, obs)

    def test2_get_library(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api.active_token = False
        api.active_token_expiration_time = time.time() + 10.0
        response_mock = MagicMock()
        response_mock.json.return_value = {}
        session.get.return_value = response_mock
        exp = "Couldn't connect to GOG servers"
        retrieved_games, obs = api.get_library()
        self.assertEqual(exp, obs)

    def test1_get_version(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        test_game = Game("Test Game", platform="linux")
        exp = "gog-2"
        obs = api.get_version(test_game, gameinfo=API_GET_INFO_TOONSTRUCK)
        self.assertEqual(exp, obs)

    def test2_get_version(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        test_game = Game("Test Game", platform="linux")
        dlc_name = "Test DLC"
        game_info = API_GET_INFO_TOONSTRUCK
        game_info["expanded_dlcs"] = [{"title": dlc_name, "downloads": {"installers": [{"os": "linux", "version": "1.2.3.4"}]}}]
        exp = "1.2.3.4"
        obs = api.get_version(test_game, gameinfo=API_GET_INFO_TOONSTRUCK, dlc_name=dlc_name)
        self.assertEqual(exp, obs)

    def test_get_download_file__info_md5(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        session.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="8acedf66c0d2986e7dee9af912b7df4f" chunks="4" timestamp="2015-07-30 17:11:12" total_size="36717998">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''
        exp = "8acedf66c0d2986e7dee9af912b7df4f"
        obs = api.get_download_file_info("url").md5
        self.assertEqual(exp, obs)

    def test_get_download_file_info_md5_returns_empty_string_on_empty_response(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        session.get().text = ""

        exp = ""
        obs = api.get_download_file_info("url").md5
        self.assertEqual(exp, obs)

    def test_get_download_file_info_md5_returns_empty_string_on_response_error(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.NOT_FOUND

        exp = ""
        obs = api.get_download_file_info("url").md5
        self.assertEqual(exp, obs)

    def test_get_download_file_info_md5_returns_empty_string_on_missing_md5(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        session.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="" chunks="4" timestamp="2015-07-30 17:11:12" total_size="36717998">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''

        exp = ""
        obs = api.get_download_file_info("url").md5
        self.assertEqual(exp, obs)

    def test_get_file_info_size(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        session.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="8acedf66c0d2986e7dee9af912b7df4f" chunks="4" timestamp="2015-07-30 17:11:12" total_size="36717998">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''
        exp = 36717998
        obs = api.get_download_file_info("url").size
        self.assertEqual(exp, obs)

    def test_get_file_info_size_returns_zero_on_empty_response(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        session.get().text = ""

        exp = 0
        obs = api.get_download_file_info("url").size
        self.assertEqual(exp, obs)

    def test_get_file_info_size_returns_zero_on_response_error(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.NOT_FOUND

        exp = 0
        obs = api.get_download_file_info("url").size
        self.assertEqual(exp, obs)

    def test_get_file_info_size_returns_zero_on_request_exception(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = requests.exceptions.RequestException("test")

        exp = 0
        obs = api.get_download_file_info("url").size
        self.assertEqual(exp, obs)

    def test_get_file_info_size_returns_zero_on_request_timeout_exception(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = requests.exceptions.ReadTimeout("test")

        exp = 0
        obs = api.get_download_file_info("url").size
        self.assertEqual(exp, obs)

    def test_get_file_info_size_returns_zero_on_missing_total_size(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"checksum": "url"}
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        session.get().text = '''<file name="gog_tis_100_2.0.0.3.sh" available="1" notavailablemsg="" md5="8acedf66c0d2986e7dee9af912b7df4f" chunks="4" timestamp="2015-07-30 17:11:12">
    <chunk id="0" from="0" to="10485759" method="md5">7e62ce101221ccdae2e9bff5c16ed9e0</chunk>
    <chunk id="1" from="10485760" to="20971519" method="md5">b80960a2546ce647bffea87f85385535</chunk>
    <chunk id="2" from="20971520" to="31457279" method="md5">5464b4499cd4368bb83ea35f895d3560</chunk>
    <chunk id="3" from="31457280" to="36717997" method="md5">0261b9225fc10c407df083f6d254c47b</chunk>
</file>'''

        exp = 0
        obs = api.get_download_file_info("url").size
        self.assertEqual(exp, obs)

    def test1_get_gamesdb_info(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request_gamesdb = MagicMock()
        api._Api__request_gamesdb.side_effect = [{}]
        test_game = Game("Test Game")
        exp = {"cover": "", "vertical_cover": "", "background": "", "genre": {}, "summary": {}}
        obs = api.get_gamesdb_info(test_game)
        self.assertEqual(exp, obs)

    def test2_get_gamesdb_info(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
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
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request_gamesdb = MagicMock()
        api._Api__request_gamesdb.side_effect = api_info

        test_game = Game("Stellaris")
        exp = copy.deepcopy(GAMESDB_INFO_STELLARIS)
        exp['genre'] = {}
        obs = api.get_gamesdb_info(test_game)
        self.assertEqual(exp, obs)

    def test_get_user_info_from_api(self):
        username = "test"
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"username": username}
        config.username = ""
        session.get.side_effect = MagicMock()
        session.get().status_code = http.HTTPStatus.OK

        obs = api.get_user_info()
        self.assertEqual(username, obs)

    def test_get_user_info_from_config(self):
        username = "test"
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {"username": "wrong"}
        config.username = username

        obs = api.get_user_info()
        self.assertEqual(username, obs)

    def test_get_user_info_return_empty_string_when_nothing_is_returned(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request = MagicMock()
        api._Api__request.return_value = {}
        config.username = ""

        exp = ""
        obs = api.get_user_info()
        self.assertEqual(exp, obs)

    def test_get_xml_data(self):
        config = MagicMock()
        session = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        session.get().text = """<file name="absolute_drift_5f6049d_65600.sh" available="1" notavailablemsg="" md5="dadbd2ca395b26c493763571dad10b7d" chunks="15" timestamp="2023-06-26 09:42:00" total_size="156521363">
	<chunk id="0" from="0" to="10485759" method="md5">1a046e241432b9d91f86ddc44b34aeb4</chunk>
	<chunk id="1" from="10485760" to="20971519" method="md5">634dd37b513c6882915f4497fc7c2997</chunk>
	<chunk id="2" from="20971520" to="31457279" method="md5">45f5b893f79d580aa44d2d2519ac1a29</chunk>
	<chunk id="3" from="31457280" to="41943039" method="md5">a2ed5b554a678b08ebeb452ef0897ae3</chunk>
	<chunk id="4" from="41943040" to="52428799" method="md5">f650b8a35eb4fc2733389c57d80dadb4</chunk>
	<chunk id="5" from="52428800" to="62914559" method="md5">c490e480f2210590fc6ba48315bf46f1</chunk>
	<chunk id="6" from="62914560" to="73400319" method="md5">aa184a1569316d0efc2e41ce48812ded</chunk>
	<chunk id="7" from="73400320" to="83886079" method="md5">5251e1872d554ee13e062c596389378d</chunk>
	<chunk id="8" from="83886080" to="94371839" method="md5">3f539fb0e641a016e51414723d9745f1</chunk>
	<chunk id="9" from="94371840" to="104857599" method="md5">4296209767474e8046351b07469e2876</chunk>
	<chunk id="10" from="104857600" to="115343359" method="md5">f5931103125d1c821f8aeb9bd89fe871</chunk>
	<chunk id="11" from="115343360" to="125829119" method="md5">32e10a9a46013f8201a3099cacb73e2f</chunk>
	<chunk id="12" from="125829120" to="136314879" method="md5">6e08694f6af5539c29f15575b6c3045b</chunk>
	<chunk id="13" from="136314880" to="146800639" method="md5">f0748e25b3970d4651e70fe3bb42f639</chunk>
	<chunk id="14" from="146800640" to="156521362" method="md5">723ada73785c66726ae747e1e2731b55</chunk>
</file>
"""
        api = Api(config, session)

        expected = DownloadInfo(
            name="absolute_drift_5f6049d_65600.sh",
            available=1,
            not_availablemsg="",
            md5="dadbd2ca395b26c493763571dad10b7d",
            chunks=[
                DownloadChunk(
                    chunk_id=0,
                    from_byte=0,
                    to_byte=10485759,
                    method="md5",
                    checksum="1a046e241432b9d91f86ddc44b34aeb4",
                ),
                DownloadChunk(
                    chunk_id=1,
                    from_byte=10485760,
                    to_byte=20971519,
                    method="md5",
                    checksum="634dd37b513c6882915f4497fc7c2997",
                ),
                DownloadChunk(
                    chunk_id=2,
                    from_byte=20971520,
                    to_byte=31457279,
                    method="md5",
                    checksum="45f5b893f79d580aa44d2d2519ac1a29",
                ),
                DownloadChunk(
                    chunk_id=3,
                    from_byte=31457280,
                    to_byte=41943039,
                    method="md5",
                    checksum="a2ed5b554a678b08ebeb452ef0897ae3",
                ),
                DownloadChunk(
                    chunk_id=4,
                    from_byte=41943040,
                    to_byte=52428799,
                    method="md5",
                    checksum="f650b8a35eb4fc2733389c57d80dadb4",
                ),
                DownloadChunk(
                    chunk_id=5,
                    from_byte=52428800,
                    to_byte=62914559,
                    method="md5",
                    checksum="c490e480f2210590fc6ba48315bf46f1",
                ),
                DownloadChunk(
                    chunk_id=6,
                    from_byte=62914560,
                    to_byte=73400319,
                    method="md5",
                    checksum="aa184a1569316d0efc2e41ce48812ded",
                ),
                DownloadChunk(
                    chunk_id=7,
                    from_byte=73400320,
                    to_byte=83886079,
                    method="md5",
                    checksum="5251e1872d554ee13e062c596389378d",
                ),
                DownloadChunk(
                    chunk_id=8,
                    from_byte=83886080,
                    to_byte=94371839,
                    method="md5",
                    checksum="3f539fb0e641a016e51414723d9745f1",
                ),
                DownloadChunk(
                    chunk_id=9,
                    from_byte=94371840,
                    to_byte=104857599,
                    method="md5",
                    checksum="4296209767474e8046351b07469e2876",
                ),
                DownloadChunk(
                    chunk_id=10,
                    from_byte=104857600,
                    to_byte=115343359,
                    method="md5",
                    checksum="f5931103125d1c821f8aeb9bd89fe871",
                ),
                DownloadChunk(
                    chunk_id=11,
                    from_byte=115343360,
                    to_byte=125829119,
                    method="md5",
                    checksum="32e10a9a46013f8201a3099cacb73e2f",
                ),
                DownloadChunk(
                    chunk_id=12,
                    from_byte=125829120,
                    to_byte=136314879,
                    method="md5",
                    checksum="6e08694f6af5539c29f15575b6c3045b",
                ),
                DownloadChunk(
                    chunk_id=13,
                    from_byte=136314880,
                    to_byte=146800639,
                    method="md5",
                    checksum="f0748e25b3970d4651e70fe3bb42f639",
                ),
                DownloadChunk(
                    chunk_id=14,
                    from_byte=146800640,
                    to_byte=156521362,
                    method="md5",
                    checksum="723ada73785c66726ae747e1e2731b55",
                ),
            ],
            timestamp=datetime.datetime.fromisoformat("2023-06-26 09:42:00"),
            total_size=156521363,
        )

        actual = api.get_xml_data("")
        self.assertEqual(expected, actual)

    def test_get_xml_data_thows_XmlException(self):
        config = MagicMock()
        session = MagicMock()
        session.get().status_code = http.HTTPStatus.OK
        api = Api(config, session)

        # First test a working one changes
        session.get().text = """<file name="gog_akalabeth_world_of_doom_2.0.0.3.sh" available="1" notavailablemsg="" md5="11a770db592af2ac463e6cdc453b555b" chunks="1" timestamp="2015-07-01 18:38:21" total_size="7569960">
	<chunk id="0" from="0" to="7569959" method="md5">11a770db592af2ac463e6cdc453b555b</chunk>
</file>"""
        api.get_xml_data("")

        # Test all kinds of exceptions
        session.get().text = """<file available="1" notavailablemsg="" md5="11a770db592af2ac463e6cdc453b555b" chunks="1" timestamp="2015-07-01 18:38:21" total_size="7569960">
	<chunk id="0" from="0" to="7569959" method="md5">11a770db592af2ac463e6cdc453b555b</chunk>
</file>"""
        self.assertRaises(XmlException, api.get_xml_data, "")

        session.get().text = """<file name="gog_akalabeth_world_of_doom_2.0.0.3.sh" available="1" notavailablemsg="" chunks="1" timestamp="2015-07-01 18:38:21" total_size="7569960">
	<chunk id="0" from="0" to="7569959" method="md5">11a770db592af2ac463e6cdc453b555b</chunk>
</file>"""
        self.assertRaises(XmlException, api.get_xml_data, "")

        session.get().text = """<file name="gog_akalabeth_world_of_doom_2.0.0.3.sh" available="1" notavailablemsg="" md5="11a770db592af2ac463e6cdc453b555b" chunks="1" total_size="7569960">
	<chunk id="0" from="0" to="7569959" method="md5">11a770db592af2ac463e6cdc453b555b</chunk>
</file>"""
        self.assertRaises(XmlException, api.get_xml_data, "")

        session.get().text = """<file name="gog_akalabeth_world_of_doom_2.0.0.3.sh" available="1" notavailablemsg="" md5="11a770db592af2ac463e6cdc453b555b" chunks="1" timestamp="2015-07-01 18:38:21">
	<chunk id="0" from="0" to="7569959" method="md5">11a770db592af2ac463e6cdc453b555b</chunk>
</file>"""
        self.assertRaises(XmlException, api.get_xml_data, "")

        session.get().text = """invalid<file name="gog_akalabeth_world_of_doom_2.0.0.3.sh" available="1" notavailablemsg="" md5="11a770db592af2ac463e6cdc453b555b" chunks="1" timestamp="2015-07-01 18:38:21" total_size="7569960">
	<chunk id="0" from="0" to="7569959" method="md5">11a770db592af2ac463e6cdc453b555b</chunk>
</file>"""
        self.assertRaises(XmlException, api.get_xml_data, "")

        session.get().text = ""
        self.assertRaises(XmlException, api.get_xml_data, "")
