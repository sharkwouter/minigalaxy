import os
import sys

from minigalaxy.ui import gtk

from tests.ui import MockGiRepository

from unittest import TestCase
from unittest.mock import MagicMock


class TestGtk(TestCase):

    def setUp(self):
        super().setUp()
        self.gi_repo = MockGiRepository()
        sys.modules['gi.repository'] = self.gi_repo
        self.pixbuf_loader = MagicMock()
        self.gi_repo.GdkPixbuf.PixbufLoader = self.pixbuf_loader
        self.pixbuf_loader.return_value = self.pixbuf_loader

        # make sure that no other test file has left the cache unclean
        gtk.PIXBUF_CACHE.clear()

    def tearDown(self):
        gtk.PIXBUF_CACHE.clear()
        del sys.modules['gi.repository']
        super().tearDown()

    def test_load_pixbuf_nocache(self):
        self.__verify_load_pixbuf(False)
        self.assertIsNone(gtk.PIXBUF_CACHE.get("icon_linux.png", None))

    def test_load_pixbuf_docache(self):
        loaded = self.__verify_load_pixbuf(True)
        # make sure that what was returned by the loaded is directly placed in cache,
        # no copies etc.
        self.assertIs(loaded, gtk.PIXBUF_CACHE.get("icon_linux.png"))

    def __verify_load_pixbuf(self, use_cache):
        self.pixbuf_loader.get_pixbuf.return_value = "LOADED_DATA"

        loaded = gtk.load_pixbuf("icon_linux.png", use_cache)
        self.assertEqual("LOADED_DATA", loaded)

        self.pixbuf_loader.write.assert_called_once()
        self.pixbuf_loader.close.assert_called_once()
        self.pixbuf_loader.get_pixbuf.assert_called_once()

        return loaded

    def test_load_pixbuf_cached(self):
        cached = "SOME CACHED DATA"
        gtk.PIXBUF_CACHE["cached_pseudo_image"] = cached
        self.pixbuf_loader.get_pixbuf.return_value = "should not reload a cached image!"
        loaded = gtk.load_pixbuf("cached_pseudo_image")

        self.assertIs(cached, loaded)
        self.pixbuf_loader.get_pixbuf.assert_not_called()

    def test_load_scaled_pixbuf_nocache(self):
        self.__verify_load_scaled_pixbuf(36, False)
        self.assertEqual({}, gtk.PIXBUF_CACHE, "Nothing should have been cached!")

    def test_load_scaled_pixbuf_docache(self):
        pixbuf, scaled = self.__verify_load_scaled_pixbuf(24, True)
        self.assertIs(pixbuf, gtk.PIXBUF_CACHE.get("icon_linux.png"))
        self.assertIs(scaled, gtk.PIXBUF_CACHE.get("icon_linux.png_24x24"))

    def test_load_scaled_pixbuf_unscaled_cached(self):
        pixbuf = MagicMock()
        scaled = "SCALED"
        pixbuf.scale_simple.return_value = scaled
        self.pixbuf_loader.get_pixbuf.return_value = "should not reload a cached image!"

        gtk.PIXBUF_CACHE["unscaled_cached"] = pixbuf
        loaded = gtk.load_scaled_pixbuf("unscaled_cached", 16)

        self.assertIs(scaled, loaded)
        self.pixbuf_loader.get_pixbuf.assert_not_called()
        pixbuf.scale_simple.assert_called_once_with(16, 16, gtk.GdkPixbuf.InterpType.BILINEAR)

    def test_load_scaled_pixbuf_both_cached(self):
        pixbuf = MagicMock()
        scaled = "SCALED"
        pixbuf.scale_simple.return_value = scaled
        self.pixbuf_loader.get_pixbuf.return_value = "should not reload a cached image!"

        gtk.PIXBUF_CACHE["unscaled_cached"] = pixbuf
        gtk.PIXBUF_CACHE["unscaled_cached_16x16"] = scaled
        loaded = gtk.load_scaled_pixbuf("unscaled_cached", 16)

        self.assertIs(scaled, loaded)
        self.pixbuf_loader.get_pixbuf.assert_not_called()
        pixbuf.scale_simple.assert_not_called()

    def __verify_load_scaled_pixbuf(self, size, use_cache):
        expected_scaled_value = f"SCALED:{size}x{size}"
        pixbuf = MagicMock()
        pixbuf.scale_simple.side_effect = lambda w, h, scale_type: f"SCALED:{w}x{h}"
        self.pixbuf_loader.get_pixbuf.return_value = pixbuf

        scaled = gtk.load_scaled_pixbuf("icon_linux.png", size, use_cache)
        self.assertEqual(expected_scaled_value, scaled)
        pixbuf.scale_simple.assert_called_once_with(size, size, gtk.GdkPixbuf.InterpType.BILINEAR)

        return pixbuf, scaled

    def test_load_ui(self):
        """
        Checks if ui files are loaded correctly by loading some of the smaller files and comparing
        the result with directly read data.
        """
        ui_data_dir = "minigalaxy/ui/data"
        ui_files = ["categoryfilters.ui", "filterswitch.ui", "download_action_buttons.ui"]
        for ui_file in ui_files:
            with self.subTest(ui_file):
                full_path = os.path.join(ui_data_dir, ui_file)
                actual = gtk.load_ui(ui_file)
                expected = ""
                with open(full_path, 'r') as reader:
                    expected = reader.read()
                self.assertEqual(expected, actual)

    def test_scale_pixbuf(self):
        pixbuf = MagicMock()
        gtk.scale_pixbuf(pixbuf, 24)
        pixbuf.scale_simple.assert_called_once_with(24, 24, gtk.GdkPixbuf.InterpType.BILINEAR)
