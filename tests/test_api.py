import http
from unittest import TestCase
from unittest.mock import MagicMock, Mock
import copy
import requests
import time
from minigalaxy.api import Api
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
API_GET_INFO_BLACKWELL = [{'id': '51437500425760439', 'game_id': '51295394952128810', 'platform_id': 'gog', 'external_id': '1207662883', 'dlcs_ids': [], 'dlcs': [], 'parent_id': None, 'supported_operating_systems': [{'slug': 'linux', 'name': 'Linux'}, {'slug': 'osx', 'name': 'macOS'}, {'slug': 'windows', 'name': 'Windows'}], 'available_languages': [{'code': 'en-US'}], 'first_release_date': '2006-12-23T00:00:00+0000', 'game': {'id': '51295394952128810', 'parent_id': None, 'dlcs_ids': [], 'first_release_date': '2006-12-23T00:00:00+0000', 'releases': [{'id': '51295394972780958', 'platform_id': 'steam', 'external_id': '80330', 'release_per_platform_id': 'steam_80330'}, {'id': '51437500425760439', 'platform_id': 'gog', 'external_id': '1207662883', 'release_per_platform_id': 'gog_1207662883'}, {'id': '52472176412391232', 'platform_id': 'humble', 'external_id': 'theblackwelllegacy', 'release_per_platform_id': 'humble_theblackwelllegacy'}, {'id': '52990950679797056', 'platform_id': 'humble', 'external_id': 'blackwelllegacy_steam', 'release_per_platform_id': 'humble_blackwelllegacy_steam'}, {'id': '54824915113880126', 'platform_id': 'amiga', 'external_id': 'blackwell1', 'release_per_platform_id': 'amiga_blackwell1'}, {'id': '56154123001776496', 'platform_id': 'humble', 'external_id': 'blackwelllegacy_bundle_steam', 'release_per_platform_id': 'humble_blackwelllegacy_bundle_steam'}, {'id': '51295394952128810', 'platform_id': 'generic', 'external_id': '51295394952128810', 'release_per_platform_id': 'generic_51295394952128810'}], 'title': {'*': 'The Blackwell Legacy', 'en-US': 'The Blackwell Legacy'}, 'sorting_title': {'*': 'Blackwell Legacy', 'en-US': 'Blackwell Legacy'}, 'type': 'game', 'developers_ids': ['51141380061810434'], 'developers': [{'id': '51141380061810434', 'name': 'Wadjet Eye Games', 'slug': 'wadjet-eye-games'}], 'publishers_ids': ['51141380061810434'], 'publishers': [{'id': '51141380061810434', 'name': 'Wadjet Eye Games', 'slug': 'wadjet-eye-games'}], 'genres_ids': ['51071842251704278', '51121492616405278', '51141224673762034', '51141224986801358'], 'genres': [{'id': '51071842251704278', 'name': {'*': 'Adventure', 'en-US': 'Adventure'}, 'slug': 'adventure'}, {'id': '51121492616405278', 'name': {'*': 'Indie', 'en-US': 'Indie'}, 'slug': 'indie'}, {'id': '51141224673762034', 'name': {'*': 'Puzzle', 'en-US': 'Puzzle'}, 'slug': 'puzzle'}, {'id': '51141224986801358', 'name': {'*': 'Point-and-click', 'en-US': 'Point-and-click'}, 'slug': 'point-and-click'}], 'themes_ids': ['51141224799400616', '51141227696328058', '51141227910729860'], 'themes': [{'id': '51141224799400616', 'name': {'*': 'Comedy', 'en-US': 'Comedy'}, 'slug': 'comedy'}, {'id': '51141227696328058', 'name': {'*': 'Mystery', 'en-US': 'Mystery'}, 'slug': 'mystery'}, {'id': '51141227910729860', 'name': {'*': 'Drama', 'en-US': 'Drama'}, 'slug': 'drama'}], 'screenshots': [{'url_format': 'https://images.gog.com/368f07e0edcce9191e60a004b0ef7bf8d9a97eac65b66e5e497f9e2728045255{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/075326e70912449e02c3d4593a26317ad8d7f8ba5f2d0d3aa216a5a467130f34{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/2c71a940d797c466a563ecfc132933300ce37bd996140dbaaf48333d2f628fb3{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/d8c490c12f0534adeb69fdeb467a4719d24765a85a58a880f9aab13008d14683{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/5724fb0d43b4b753e89a6dec52b40a8c401396d6b5ecaa228115a3b06c5fd374{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/7478e2b53e403ee04eb27331ecebad0d6e3403e76c747fffd6f5b2303005b174{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/bd6f6ba043f9ae0883c196086841891ac5ed11dcf933ab2ca3f104312be10802{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/c37db76ad0d3f6471a5bbac1cc5a17393ee5a2c8ae16150cc221aac5855dd788{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/9ec05f3b79a0e3bd9a2b4eb29788222b5723feb6273b6a0bbb711d53d6a93b25{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/7376efd38b2aa383e16d066c6cfbc78fefa9b870f91033666a08bef85bac6db9{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/78145ccd85eca1fec952a464b3b9aeea7b5288518282e8194e3a0991fd9aef77{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/d46d89dfabe116db2f428138d3a3481faf91e00759ef97e02645da8f2652df3a{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/01e93965ea0ce72fdb50472e08a11924a9c5aa45f86a6aed4deeff987010df34{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/c2f064852161738df48918111327c108cdb014bffff487caa13caa2f7c2d5750{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/5cedd80d5f46fa20d4f95e9b8305d608b44c098b4741d2347e0365c2c9932cda{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/b80f003398c1d4e63ae2054665ee90785a9ea526b371859269e92c51ac7840c1{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/702fe48f311ef0d398e219cf28eda78b64bf3104dda937983b7ec621d0845caa{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/73b9adb70ec1c2bfc75cd6286a4b1f5c81959a4e25ce4e0527dd9a61d28c7953{formatter}.{ext}?namespace=gamesdb'}], 'videos': [{'provider': 'youtube', 'video_id': 'j026WKDQhi8', 'thumbnail_id': 'j026WKDQhi8', 'name': 'Trailer'}], 'artworks': [{'url_format': 'https://images.gog.com/19eba3c8303ce3cdb45cc9f2f94993efd2620f7f12eeac814512e64d26e88f0f{formatter}.{ext}?namespace=gamesdb'}, {'url_format': 'https://images.gog.com/978a934689c303511c425450c62db88edd11ac4da9026d801159decf605cd93e{formatter}.{ext}?namespace=gamesdb'}], 'summary': {'*': "omitted for test", 'en-US': "omitted for test"}, 'visible_in_library': True, 'aggregated_rating': 70, 'game_modes': [{'id': '53051895165351137', 'name': 'Single player', 'slug': 'single-player'}], 'horizontal_artwork': {'url_format': 'https://images.gog.com/e6e6d9001ec0c990327bd8f20630b5e39d0b5d33f69778163025d9d7b04f3c44{formatter}.{ext}?namespace=gamesdb'}, 'background': {'url_format': 'https://images.gog.com/e6e6d9001ec0c990327bd8f20630b5e39d0b5d33f69778163025d9d7b04f3c44{formatter}.{ext}?namespace=gamesdb'}, 'vertical_cover': {'url_format': 'https://images.gog.com/87f87afa3a55ca5eb59df9a66c5063c202281432262b3f0fe8ef8e324270df61{formatter}.{ext}?namespace=gamesdb'}, 'cover': {'url_format': 'https://images.gog.com/87f87afa3a55ca5eb59df9a66c5063c202281432262b3f0fe8ef8e324270df61{formatter}.{ext}?namespace=gamesdb'}, 'logo': {'url_format': 'https://images.gog.com/a82f4f793fc7e981b7a8d429508b11ba7ec5783f3ae5db6a8d3508bd139ba122{formatter}.{ext}?namespace=gamesdb'}, 'square_icon': {'url_format': 'https://images.gog.com/978a934689c303511c425450c62db88edd11ac4da9026d801159decf605cd93e{formatter}.{ext}?namespace=gamesdb'}, 'global_popularity_all_time': 0, 'global_popularity_current': 0, 'series': {'id': '53060497266141230', 'name': 'Blackwell', 'slug': 'blackwell'}}, 'title': {'*': 'Blackwell Legacy', 'en-US': 'The Blackwell Legacy'}, 'sorting_title': {'*': 'Blackwell Legacy', 'en-US': 'Blackwell Legacy'}, 'type': 'game', 'summary': {'*': "When Rosa Blackwell's only relative dies after twenty years in a coma, she thinks the worst is over.  This all changes when Joey Mallone, a sardonic ghost from the 1930s, blows into her life and tells her that she is a medium.  Whether they like it or not, it is up to them to cure the supernatural ills of New York in this critically-acclaimed series of point-and-click adventure games. \r\nWhen three NYU students kill themselves one after the other, nobody thinks that a sinister force is at work.  Nobody but fledgling medium Rosa Blackwell and her new spirit guide Joey Mallone.  It's trial by fire as they set these troubled spirits to rest.", 'en-US': "When Rosa Blackwell's only relative dies after twenty years in a coma, she thinks the worst is over. This all changes when Joey Mallone, a sardonic ghost from the 1930s, blows into her life and tells her that she is a medium. Whether they like it or not, it is up to them to cure the supernatural ills of New York in this critically-acclaimed series of point-and-click adventure games.\nWhen three NYU students kill themselves one after the other, nobody thinks that a sinister force is at work. Nobody but fledgling medium Rosa Blackwell and her new spirit guide Joey Mallone. It's trial by fire as they set these troubled spirits to rest."}, 'videos': [{'provider': 'youtube', 'video_id': 'vkinYRD5sr4', 'thumbnail_id': 'vkinYRD5sr4', 'name': None}, {'provider': 'youtube', 'video_id': 'gLcoCPfc1zE', 'thumbnail_id': 'gLcoCPfc1zE', 'name': None}], 'game_modes': [{'id': '53051895165351137', 'name': 'Single player', 'slug': 'single-player'}], 'logo': {'url_format': 'https://images.gog.com/a82f4f793fc7e981b7a8d429508b11ba7ec5783f3ae5db6a8d3508bd139ba122{formatter}.{ext}?namespace=gamesdb'}, 'series': {'id': '53060497266141230', 'name': 'Blackwell', 'slug': 'blackwell'}}]
GAMESDB_INFO_BLACKWELL = {'background': 'https://images.gog.com/e6e6d9001ec0c990327bd8f20630b5e39d0b5d33f69778163025d9d7b04f3c44.png?namespace=gamesdb','cover': 'https://images.gog.com/87f87afa3a55ca5eb59df9a66c5063c202281432262b3f0fe8ef8e324270df61.png?namespace=gamesdb','genre': {'*': 'Adventure, Indie, Puzzle, Point-and-click', 'en-US': 'Adventure, Indie, Puzzle, Point-and-click'},'summary': {'*': 'omitted for test', 'en-US': 'omitted for test'},'vertical_cover': 'https://images.gog.com/87f87afa3a55ca5eb59df9a66c5063c202281432262b3f0fe8ef8e324270df61.png?namespace=gamesdb'}


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

    def test_get_gamesdb_info_with_multiple_genres(self):
        session = MagicMock()
        config = MagicMock()
        api = Api(config, session)
        api._Api__request_gamesdb = MagicMock()
        api._Api__request_gamesdb.side_effect = API_GET_INFO_BLACKWELL
        test_game = Game("Blackwell Legacy")
        exp = GAMESDB_INFO_BLACKWELL
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
