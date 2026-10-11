import os

from unittest import TestCase, mock

from minigalaxy.file_utils import get_available_disk_space, make_tmp_dir
from minigalaxy.game import Game
from minigalaxy.paths import CACHE_DIR


class TestFileUtils(TestCase):

    @mock.patch('os.statvfs')
    def test_get_availablediskspace(self, mock_os_statvfs):
        frsize = 4096
        bavail = 29699296
        mock_os_statvfs().f_frsize = frsize
        mock_os_statvfs().f_bavail = bavail
        exp = frsize * bavail
        obs = get_available_disk_space("/")
        self.assertEqual(exp, obs)

    def test_make_tmp_dir_target_not_existing(self):
        test_id = id(self)
        expected = os.path.join(CACHE_DIR, str(test_id))

        test_game = Game(name="something", game_id=test_id)
        err, created_dir = make_tmp_dir(test_game)
        was_created = os.path.exists(created_dir)

        if was_created:
            os.rmdir(created_dir)

        self.assertEqual("", err, "There should be no error message when creating a temp dir")
        self.assertEqual(expected, created_dir)
        self.assertTrue(was_created, f"make_tmp_dir failed to create '{expected}'")
