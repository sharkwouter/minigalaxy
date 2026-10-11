import os

from unittest import TestCase, mock

from minigalaxy.file_utils import get_available_disk_space, make_tmp_dir
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
        test_name = str(id(self))
        expected = os.path.join(CACHE_DIR, "test", test_name)

        created_dir = make_tmp_dir(test_name, temp_type="test")
        was_created = os.path.exists(created_dir)

        if was_created:
            os.rmdir(created_dir)

        self.assertEqual(expected, created_dir)
        self.assertTrue(was_created, f"make_tmp_dir failed to create '{expected}'")
