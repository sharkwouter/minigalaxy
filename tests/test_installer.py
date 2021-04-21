import copy
from unittest import TestCase, mock
from unittest.mock import patch, mock_open, MagicMock

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
        obs = installer.get_available_disk_space("/")
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
        bavail = 29699
        mock_os_statvfs().f_frsize = frsize
        mock_os_statvfs().f_bavail = bavail
        exp = False
        obs = installer.check_diskspace(524288000, "/")
        self.assertEqual(exp, obs)

    @mock.patch('os.statvfs')
    def test1_verifie_disk_space(self, mock_os_statvfs):
        frsize = 4096
        bavail = 29699
        mock_os_statvfs().f_frsize = frsize
        mock_os_statvfs().f_bavail = bavail
        backup_installer = copy.deepcopy(installer.get_game_size_from_unzip)
        installer.get_game_size_from_unzip = MagicMock()
        installer.get_game_size_from_unzip.return_value = 524288000
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky", platform="linux")
        installer_file = "/beneath_a_steel_sky_en_gog_2_20150.sh"
        exp = "Not enough space to extract game. Required: 524288000 Available: 121647104"
        obs = installer.verifie_disk_space(game, installer_file)
        installer.get_game_size_from_unzip = backup_installer
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    def test_get_game_size_from_unzip(self, mock_subprocess):
        stdout = b"""  550557  Defl:N   492111  11% 2018-04-19 15:01 48d4ab3f  meta/gtk-2.0/pixmaps/background.png
       0  Stored        0   0% 2018-04-19 15:01 00000000  scripts/
  212070  Defl:N    63210  70% 2017-10-25 11:07 a05c1728  scripts/localization.lua
   21572  Defl:N     5592  74% 2017-06-27 13:02 e47c0968  scripts/mojosetup_init.lua
    9171  Defl:N     3374  63% 2017-10-25 11:07 14ac8da7  scripts/app_localization.lua
    4411  Defl:N     1247  72% 2018-04-19 15:01 2405a519  scripts/config.lua
   76365  Defl:N    17317  77% 2017-10-25 11:07 27d8bdb2  scripts/mojosetup_mainline.lua
--------          -------  ---                            -------
159236636         104883200  34%                            189 files
"""
        mock_subprocess().communicate.return_value = [stdout, b"stderr"]
        installer_path = "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        exp = 159236636
        obs = installer.get_game_size_from_unzip(installer_path)
        self.assertEqual(exp, obs)
