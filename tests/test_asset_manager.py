"""
Test the asset_manager module

Similar to the test_api.py test suite, we mock out the API calls
In addition, we mock filesystem calls and Gtk calls.
"""
from datetime import datetime, timedelta
import math
import os
import sys
import time
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

m_constants = MagicMock()
m_config = MagicMock()
m_paths = MagicMock()
m_gtk = MagicMock()
m_gi = MagicMock()
m_gametile = MagicMock()
m_library = MagicMock()
m_preferences = MagicMock()
m_login = MagicMock()
m_about = MagicMock()
m_window = MagicMock()

sys.modules['minigalaxy.constants'] = m_constants
sys.modules['minigalaxy.config'] = m_config
sys.modules['minigalaxy.paths'] = m_paths
sys.modules['minigalaxy.ui.window'] = m_window
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.gametile'] = m_gametile


class UnitTestGtkTemplate:

    def __init__(self):
        self.Child = m_gtk

    def from_file(self, lib_file):
        def passthrough(func):
            def passthrough2():
                return func()
            return passthrough2
        return passthrough

    Callback = MagicMock()


class UnitTestGiRepository:

    class Gtk:
        Template = UnitTestGtkTemplate()
        Widget = MagicMock()
        Settings = MagicMock()
        ResponseType = MagicMock()

        class ApplicationWindow:
            def __init__(self, title):
                pass

            set_default_icon_list = MagicMock()
            show_all = MagicMock()

    Gdk = MagicMock()
    GdkPixbuf = MagicMock()
    Gio = MagicMock()
    GLib = MagicMock


u_gi_repository = UnitTestGiRepository()
sys.modules['gi.repository'] = u_gi_repository
sys.modules['gi'] = m_gi
sys.modules['minigalaxy.ui.library'] = m_library
sys.modules['minigalaxy.ui.preferences'] = m_preferences
sys.modules['minigalaxy.ui.login'] = m_login
sys.modules['minigalaxy.ui.about'] = m_about
sys.modules['minigalaxy.ui.gtk'] = u_gi_repository

from minigalaxy.api import Api                         # noqa: E402
from minigalaxy.game import Game                       # noqa: E402
from minigalaxy.paths import COVER_DIR                 # noqa: E402
from minigalaxy.asset_manager import Asset, AssetType  # noqa: E402

API_GET_INFO_STELLARIS = [{'id': '51622789000874509', 'game_id': '51154268886064420', 'platform_id': 'gog', 'external_id': '1508702879', 'game': {'genres': [{'id': '51071904337940794', 'name': {'*': 'Strategy', 'en-US': 'Strategy'}, 'slug': 'strategy'}], 'summary': {'*': 'Stellaris description'}, 'visible_in_library': True, 'aggregated_rating': 78.5455, 'game_modes': [{'id': '53051895165351137', 'name': 'Single player', 'slug': 'single-player'}, {'id': '53051908711988230', 'name': 'Multiplayer', 'slug': 'multiplayer'}], 'horizontal_artwork': {'url_format': 'https://images.gog.com/742acfb77ec51ca48c9f96947bf1fc0ad8f0551c9c9f338021e8baa4f08e449f{formatter}.{ext}?namespace=gamesdb'}, 'background': {'url_format': 'https://images.gog.com/742acfb77ec51ca48c9f96947bf1fc0ad8f0551c9c9f338021e8baa4f08e449f{formatter}.{ext}?namespace=gamesdb'}, 'vertical_cover': {'url_format': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2{formatter}.{ext}?namespace=gamesdb'}, 'cover': {'url_format': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2{formatter}.{ext}?namespace=gamesdb'}, 'logo': {'url_format': 'https://images.gog.com/c50a5d26c42d84b4b884976fb89d10bb3e97ebda0c0450285d92b8c50844d788{formatter}.{ext}?namespace=gamesdb'}, 'icon': {'url_format': 'https://images.gog.com/c85cf82e6019dd52fcdf1c81d17687dd52807835f16aa938abd2a34e5d9b99d0{formatter}.{ext}?namespace=gamesdb'}, 'square_icon': {'url_format': 'https://images.gog.com/c3adc81bf37f1dd89c9da74c13967a08b9fd031af4331750dbc65ab0243493c8{formatter}.{ext}?namespace=gamesdb'}}}]
GAMESDB_INFO_STELLARIS = {'cover': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb', 'vertical_cover': 'https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb', 'background': 'https://images.gog.com/742acfb77ec51ca48c9f96947bf1fc0ad8f0551c9c9f338021e8baa4f08e449f.png?namespace=gamesdb', 'summary': {'*': 'Stellaris description'}, 'genre': {'*': 'Strategy', 'en-US': 'Strategy'}}


class TestAsset(TestCase):
    """
    Test the AssetManager classes
    """
    def setUp(self):
        """
        Use the same API request mock for most of the tests
        """
        api = Api()
        api._Api__request_gamesdb = MagicMock()
        api._Api__request_gamesdb.side_effect = API_GET_INFO_STELLARIS
        api.get_info = MagicMock()
        api.get_info.return_value = API_GET_INFO_STELLARIS
        test_game = Game("Stellaris")
        self.api_info = api.get_info(test_game)
        self.gamesdb_info = api.get_gamesdb_info(test_game)

    def test_asset_parses_gamedb(self):
        """
        Test that the Asset class creates and Asset and generates correct
        filenames from URLs.
        """
        asset = Asset(AssetType.COVER, self.gamesdb_info["cover"],
                      {"game_id": self.api_info[0]["id"],
                       "game_installed": False})

        self.assertEqual(asset.url, "https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb")
        self.assertEqual(asset.url_file_extension(), "png")
        self.assertEqual(asset.filename, os.path.join(COVER_DIR, "51622789000874509.png"))

    @patch('os.path')
    def test_asset_file_exists(self, path_mock):
        """
        Test that the Asset class correctly checks existence for files
        """
        fn = os.path.join(COVER_DIR, "51622789000874509.png")
        path_mock.exists.return_value = True

        asset = Asset(AssetType.COVER, self.gamesdb_info["cover"],
                      {"game_id": self.api_info[0]["id"],
                       "game_installed": False})

        self.assertEqual(asset.url, "https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb")
        self.assertEqual(asset.filename, os.path.join(COVER_DIR, "51622789000874509.png"))
        self.assertEqual(asset.exists(), True)
        path_mock.exists.assert_called_with(fn)

    @patch('os.path')
    def test_asset_file_doesnt_exist(self, path_mock):
        """
        Test that the Asset class correctly checks for existence of files
        """
        fn = os.path.join(COVER_DIR, "51622789000874509.png")
        path_mock.exists.return_value = False

        asset = Asset(AssetType.COVER, self.gamesdb_info["cover"],
                      {"game_id": self.api_info[0]["id"],
                       "game_installed": False})

        self.assertEqual(asset.url, "https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb")
        self.assertEqual(asset.filename, os.path.join(COVER_DIR, "51622789000874509.png"))
        self.assertEqual(asset.exists(), False)
        path_mock.exists.assert_called_with(fn)

    @patch('os.path')
    @patch('os.stat')
    def test_asset_not_expired(self, stat_mock, path_mock):
        """
        Test that the Asset class correctly checks that files are not expired
        """
        path_mock.exists.return_value = True

        # Using datetime.now() for testing, this makes some assumptions like our test
        # doesn't run longer than the cache expiration time we set
        stat_result = SimpleNamespace(st_mode=33188, st_ino=7876932, st_dev=234881026,
                                      st_nlink=1, st_uid=501, st_gid=501, st_size=264,
                                      st_atime=1297230295, st_mtime=math.floor(time.time()),
                                      st_ctime=1297230027)

        stat_mock.return_value = stat_result

        asset = Asset(AssetType.COVER, self.gamesdb_info["cover"],
                      {"game_id": self.api_info[0]["id"],
                       "game_installed": False})

        self.assertEqual(asset.url, "https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb")
        self.assertEqual(asset.filename, os.path.join(COVER_DIR, "51622789000874509.png"))
        self.assertEqual(asset.exists(), True)
        self.assertEqual(asset.expired(), False)

    @patch('os.path')
    @patch('os.stat')
    def test_asset_expired(self, stat_mock, path_mock):
        """
        Test that the Asset class correctly checks that files are expired
        """
        path_mock.exists.return_value = True

        # Using datetime.now() for testing, this makes some assumptions like our test
        # doesn't run longer than the cache expiration time we set
        stat_result = SimpleNamespace(st_mode=33188, st_ino=7876932, st_dev=234881026,
                                      st_nlink=1, st_uid=501, st_gid=501, st_size=264,
                                      st_atime=1297230295,
                                      st_mtime=math.floor((datetime.now() - timedelta(days=2)).timestamp()),
                                      st_ctime=1297230027)

        stat_mock.return_value = stat_result

        asset = Asset(AssetType.COVER, self.gamesdb_info["cover"],
                      {"game_id": self.api_info[0]["id"],
                       "game_installed": False})

        self.assertEqual(asset.url, "https://images.gog.com/8d822a05746670fb2540e9c136f0efaed6a2d5ab698a9f8bd7f899d21f2022d2.png?namespace=gamesdb")
        self.assertEqual(asset.filename, os.path.join(COVER_DIR, "51622789000874509.png"))
        self.assertEqual(asset.exists(), True)
        self.assertEqual(asset.expired(), True)
