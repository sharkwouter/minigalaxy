from unittest import TestCase, mock
from unittest.mock import patch, mock_open

from minigalaxy.game import Game
from minigalaxy import installer
from minigalaxy.translation import _


class Test(TestCase):
    @mock.patch('os.path.exists')
    @mock.patch('hashlib.md5')
    @mock.patch('os.listdir')
    def test1_verify_installer_integrity(self, mock_listdir, mock_hash, mock_is_file):
        md5_sum = "5cc68247b61ba31e37e842fd04409d98"
        installer_name = "beneath_a_steel_sky_en_gog_2_20150.sh"
        mock_is_file.return_value = True
        mock_hash().hexdigest.return_value = md5_sum
        mock_listdir.return_value = [installer_name]
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky",
                    md5sum={installer_name: md5_sum})
        installer_path = "/home/user/.cache/minigalaxy/download/" \
                         "Beneath a Steel Sky/{}".format(installer_name)
        exp = ""
        with patch("builtins.open", mock_open(read_data=b"")):
            obs = installer.verify_installer_integrity(game, installer_path)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('hashlib.md5')
    @mock.patch('os.listdir')
    def test2_verify_installer_integrity(self, mock_listdir, mock_hash, mock_is_file):
        md5_sum = "5cc68247b61ba31e37e842fd04409d98"
        installer_name = "beneath_a_steel_sky_en_gog_2_20150.sh"
        corrupted_md5_sum = "99999947b61ba31e37e842fd04409d98"
        mock_is_file.return_value = True
        mock_hash().hexdigest.return_value = corrupted_md5_sum
        mock_listdir.return_value = [installer_name]
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky",
                    md5sum={installer_name: md5_sum})
        installer_path = "/home/user/.cache/minigalaxy/download/" \
                         "Beneath a Steel Sky/{}".format(installer_name)
        exp = _("{} was corrupted. Please download it again.").format(installer_name)
        with patch("builtins.open", mock_open(read_data=b"aaaa")):
            obs = installer.verify_installer_integrity(game, installer_path)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('os.listdir')
    @mock.patch('subprocess.Popen')
    def test1_extract_installer(self, mock_subprocess, mock_listdir, mock_is_file):
        mock_is_file.return_value = True
        mock_subprocess().returncode = 0
        mock_subprocess().communicate.return_value = [b"stdout", b"stderr"]
        mock_listdir.return_value = ["object1", "object2"]
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky")
        installer_path = "/home/makson/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1207658695"
        exp = ""
        obs = installer.extract_installer(game, installer_path, temp_dir)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('os.listdir')
    @mock.patch('subprocess.Popen')
    def test2_extract_installer(self, mock_subprocess, mock_listdir, mock_is_file):
        mock_is_file.return_value = True
        mock_subprocess().returncode = 2
        mock_subprocess().communicate.return_value = [b"stdout", b"stderr"]
        mock_listdir.return_value = ["object1", "object2"]
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky")
        installer_path = "/home/makson/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1207658695"
        exp = "The installation of /home/makson/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh failed. Please try again."
        obs = installer.extract_installer(game, installer_path, temp_dir)
        self.assertEqual(exp, obs)

    @mock.patch('os.statvfs')
    def test_get_availablediskspace(self, mock_os_statvfs):
        frsize = 4096
        bavail = 29699296
        mock_os_statvfs().f_frsize = frsize
        mock_os_statvfs().f_bavail = bavail
        exp = frsize * bavail
        obs = installer.get_availablediskspace("/")
        self.assertEqual(exp, obs)

    @mock.patch('os.statvfs')
    def test1_check_diskspace(self, mock_os_statvfs):
        frsize = 4096
        bavail = 29699296
        mock_os_statvfs().f_frsize = frsize
        mock_os_statvfs().f_bavail = bavail
        exp = True
        obs = installer.check_diskspace(524288000, "/")
        self.assertEqual(exp, obs)

    @mock.patch('os.statvfs')
    def test2_check_diskspace(self, mock_os_statvfs):
        frsize = 4096
        bavail = 296992
        mock_os_statvfs().f_frsize = frsize
        mock_os_statvfs().f_bavail = bavail
        exp = False
        obs = installer.check_diskspace(524288000, "/")
        self.assertEqual(exp, obs)
