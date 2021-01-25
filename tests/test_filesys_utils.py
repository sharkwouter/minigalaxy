import sys
import unittest
from unittest import TestCase
from unittest.mock import MagicMock, patch, mock_open

m_paths = MagicMock()
m_paths.CONFIG_DIR = "/home/user/.config/minigalaxy"
m_paths.CACHE_DIR = "/home/user/.cache/minigalaxy"
sys.modules['minigalaxy.paths'] = m_paths
from minigalaxy import filesys_utils


class Test(TestCase):

# For some reasons tis doesn't work well for now.
#    @unittest.mock.patch("os.path.exists")
#    def test__get_white_list(self, m_os_path_exists):
#        m_os_path_exists.side_effect = [True]
#        json_content = '{"install_dir": "/home/user/GoG Games"}'
#        with patch("builtins.open", mock_open(read_data=json_content)):
#            from minigalaxy import filesys_utils
#            obs = filesys_utils._get_white_list()
#        exp = ["/home/user/GoG Games", "/home/user/.config/minigalaxy", "/home/user/.cache/minigalaxy"]
#        self.assertEqual(exp, obs)

    @unittest.mock.patch("subprocess.check_output")
    def test__get_black_list(self, m_check_output):
        m_check_output.side_effect = [b"/home/user", b"/home/user/Pulpit", b"/home/user/Dokumenty",
                                               b"/home/user/Pobrane", b"/home/user/Muzyka", b"/home/user/Obrazy",
                                               b"/home/user/Publiczny", b"/home/user/Szablony", b"/home/user/Wideo"]
        exp = ["/home/user", "/home/user/Pulpit", "/home/user/Dokumenty", "/home/user/Pobrane",
               "/home/user/Muzyka", "/home/user/Obrazy", "/home/user/Publiczny", "/home/user/Szablony",
               "/home/user/Wideo"]
        obs = filesys_utils._get_black_list()
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._get_white_list")
    @unittest.mock.patch("minigalaxy.filesys_utils._get_black_list")
    def test1__check_if_accordance_with_lists(self, m_get_black_list, m_get_white_list):
        m_get_white_list.return_value = ["/home/user/GoG Games"]
        m_get_black_list.return_value = ["/home/user"]
        exp = "/home/user/Non_White_List_Dir is not inside white list for file operations."
        obs = filesys_utils._check_if_accordance_with_lists("/home/user/Non_White_List_Dir")
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._get_white_list")
    @unittest.mock.patch("minigalaxy.filesys_utils._get_black_list")
    def test2__check_if_accordance_with_lists(self, m_get_black_list, m_get_white_list):
        m_get_white_list.return_value = ["/home/user/GoG Games", "/home/user"]
        m_get_black_list.return_value = ["/home/user"]
        exp = "/home/user is on black list for file operations."
        obs = filesys_utils._check_if_accordance_with_lists("/home/user")
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._get_white_list")
    @unittest.mock.patch("minigalaxy.filesys_utils._get_black_list")
    def test3__check_if_accordance_with_lists(self, m_get_black_list, m_get_white_list):
        m_get_white_list.return_value = ["/home/user/GoG Games"]
        m_get_black_list.return_value = ["/home/user"]
        exp = ""
        obs = filesys_utils._check_if_accordance_with_lists("/home/user/GoG Games")
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._check_if_accordance_with_lists")
    @unittest.mock.patch("os.path.exists")
    @unittest.mock.patch("os.path.isdir")
    def test1__check_if_ok_for_copy_or_move(self, m_os_path_isdir, m_os_path_exists, m_check_if_accordance_with_lists):
        source = "/home/user/.cache/minigalaxy/game1"
        target = "/home/user/GoG Games/game1"
        recursive = False
        overwrite = False
        m_check_if_accordance_with_lists.return_value = ""
        m_os_path_exists.side_effect = [True, False]
        m_os_path_isdir.side_effect = [True, False]
        exp = ""
        obs = filesys_utils._check_if_ok_for_copy_or_move(source=source, target=target, recursive=recursive,
                                                          overwrite=overwrite)
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._check_if_accordance_with_lists")
    @unittest.mock.patch("os.path.exists")
    @unittest.mock.patch("os.path.isdir")
    def test2__check_if_ok_for_copy_or_move(self, m_os_path_isdir, m_os_path_exists, m_check_if_accordance_with_lists):
        source = "/home/user/.cache/minigalaxy/game1"
        target = "/home/user/GoG Games/game1"
        recursive = False
        overwrite = False
        m_check_if_accordance_with_lists.return_value = ""
        m_os_path_exists.side_effect = [False, False]
        m_os_path_isdir.side_effect = [True, False]
        exp = "No such a file or directory: /home/user/.cache/minigalaxy/game1"
        obs = filesys_utils._check_if_ok_for_copy_or_move(source=source, target=target, recursive=recursive,
                                                          overwrite=overwrite)
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._check_if_accordance_with_lists")
    @unittest.mock.patch("os.path.exists")
    @unittest.mock.patch("os.path.isdir")
    def test3__check_if_ok_for_copy_or_move(self, m_os_path_isdir, m_os_path_exists, m_check_if_accordance_with_lists):
        source = "/home/user/.cache/minigalaxy/game1"
        target = "/home/user/GoG Games/game1"
        recursive = False
        overwrite = False
        m_check_if_accordance_with_lists.return_value = ""
        m_os_path_exists.side_effect = [True, False]
        m_os_path_isdir.side_effect = [False, False]
        exp = "Directory for target operation doesn't exists: /home/user/GoG Games"
        obs = filesys_utils._check_if_ok_for_copy_or_move(source=source, target=target, recursive=recursive,
                                                          overwrite=overwrite)
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._check_if_accordance_with_lists")
    @unittest.mock.patch("os.path.exists")
    @unittest.mock.patch("os.path.isdir")
    def test4__check_if_ok_for_copy_or_move(self, m_os_path_isdir, m_os_path_exists, m_check_if_accordance_with_lists):
        source = "/home/user/.cache/minigalaxy/game1"
        target = "/home/user/GoG Games/game1"
        recursive = False
        overwrite = False
        m_check_if_accordance_with_lists.return_value = ""
        m_os_path_exists.side_effect = [True, False]
        m_os_path_isdir.side_effect = [True, True]
        exp = "Non recursive requested on directory: /home/user/GoG Games/game1"
        obs = filesys_utils._check_if_ok_for_copy_or_move(source=source, target=target, recursive=recursive,
                                                          overwrite=overwrite)
        self.assertEqual(exp, obs)

    @unittest.mock.patch("minigalaxy.filesys_utils._check_if_accordance_with_lists")
    @unittest.mock.patch("os.path.exists")
    @unittest.mock.patch("os.path.isdir")
    def test5__check_if_ok_for_copy_or_move(self, m_os_path_isdir, m_os_path_exists, m_check_if_accordance_with_lists):
        source = "/home/user/.cache/minigalaxy/game1"
        target = "/home/user/GoG Games/game1"
        recursive = False
        overwrite = False
        m_check_if_accordance_with_lists.return_value = ""
        m_os_path_exists.side_effect = [True, True]
        m_os_path_isdir.side_effect = [True, False]
        exp = "Non overwrite operation, but target exists:/home/user/GoG Games/game1"
        obs = filesys_utils._check_if_ok_for_copy_or_move(source=source, target=target, recursive=recursive,
                                                          overwrite=overwrite)
        self.assertEqual(exp, obs)


if "minigalaxy.paths" in sys.modules:
    del sys.modules["minigalaxy.paths"]