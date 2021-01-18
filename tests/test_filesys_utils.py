import sys
import unittest
from unittest import TestCase
from unittest.mock import MagicMock

m_constants = MagicMock()
m_config = MagicMock()
sys.modules['minigalaxy.constants'] = m_constants
sys.modules['minigalaxy.config'] = m_config
from minigalaxy import filesys_utils


class Test(TestCase):
    def test__get_white_list(self):
        m_config.Config.get.return_value = "/home/user/GoG Games"
        exp = ["/home/user/GoG Games", "/home/makson/.config/minigalaxy", "/home/makson/.cache/minigalaxy"]
        obs = filesys_utils._get_white_list()
        self.assertEqual(exp, obs)

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


del sys.modules['minigalaxy.constants']
del sys.modules['minigalaxy.config']
# del sys.modules["minigalaxy.game"]
