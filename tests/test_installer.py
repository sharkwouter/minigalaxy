import copy
from unittest import TestCase, mock
from unittest.mock import patch, mock_open, MagicMock

from minigalaxy.game import Game
from minigalaxy import installer
from minigalaxy.translation import _


class Test(TestCase):
    @mock.patch('shutil.which')
    def test_install_game(self, mock_which):
        """[scenario: unhandled error]"""
        mock_which.side_effect = FileNotFoundError("Testing unhandled errors during install")
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        exp = "Unhandled error."
        obs = installer.install_game(game, installer="", language="", install_dir="", keep_installers=False, create_desktop_file=True)
        self.assertEqual(exp, obs)

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
        """[scenario: linux installer, unpack success]"""
        mock_is_file.return_value = True
        mock_subprocess().poll.return_value = 0
        mock_subprocess().stdout.readlines.return_value = ["\n"]
        mock_listdir.return_value = ["object1", "object2"]
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky")
        installer_path = "/home/makson/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1207658695"
        exp = ""
        obs = installer.extract_installer(game, installer_path, temp_dir, "en", use_innoextract=False)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('os.listdir')
    @mock.patch('subprocess.Popen')
    def test2_extract_installer(self, mock_subprocess, mock_listdir, mock_is_file):
        """[scenario: linux installer, unpack failed]"""
        mock_is_file.return_value = True
        mock_subprocess().poll.return_value = 2
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        mock_listdir.return_value = ["object1", "object2"]
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky")
        installer_path = "/home/makson/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1207658695"
        exp = "The installation of /home/makson/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh failed. Please try again."
        obs = installer.extract_installer(game, installer_path, temp_dir, "en", use_innoextract=False)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    @mock.patch('shutil.which')
    def test3_extract_installer(self, mock_which, mock_subprocess):
        """[scenario: innoextract, unpack success]"""
        mock_which.return_value = True
        mock_subprocess().poll.return_value = 0
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1136126792"
        exp = ""
        obs = installer.extract_installer(game, installer_path, temp_dir, "en", use_innoextract=True)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('os.listdir')
    @mock.patch('subprocess.Popen')
    def test_extract_linux(self, mock_subprocess, mock_listdir, mock_is_file):
        mock_is_file.return_value = True
        mock_subprocess().poll.return_value = 1
        mock_subprocess().stdout.readlines.return_value = ["stdout", "(attempting to process anyway)"]
        mock_listdir.return_value = ["object1", "object2"]
        installer_path = "/home/makson/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1207658695"
        exp = ""
        obs = installer.extract_linux(installer_path, temp_dir)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    def test_extract_windows(self, mock_subprocess):
        """[scenario: innoextract, unpack success]"""
        mock_subprocess().poll.return_value = 0
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1136126792"
        exp = ""
        obs = installer.extract_windows(game, installer_path, temp_dir, "en", use_innoextract=True)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    def test1_extract_by_innoextract(self, mock_subprocess):
        """[scenario: success]"""
        mock_subprocess().poll.return_value = 0
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1136126792"
        exp = ""
        obs = installer.extract_by_innoextract(installer_path, temp_dir, "en", use_innoextract=True)
        self.assertEqual(exp, obs)

    def test2_extract_by_innoextract(self):
        """[scenario: not installed/disabled]"""
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1136126792"
        exp = "Innoextract not installed."
        obs = installer.extract_by_innoextract(installer_path, temp_dir, "en", use_innoextract=False)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    def test3_extract_by_innoextract(self, mock_subprocess):
        """[scenario: unpack failed]"""
        mock_subprocess().poll.return_value = 1
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1136126792"
        exp = "Innoextract extraction failed."
        obs = installer.extract_by_innoextract(installer_path, temp_dir, "en", use_innoextract=True)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    @mock.patch("os.path.exists")
    @mock.patch("os.symlink")
    def test1_extract_by_wine(self, mock_symlink, mock_path_exists, mock_subprocess):
        """[scenario: success]"""
        mock_path_exists.return_value = True
        mock_subprocess().poll.return_value = 0
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1136126792"
        exp = ""
        obs = installer.extract_by_wine(game, installer_path, temp_dir)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    @mock.patch("os.path.exists")
    @mock.patch("os.unlink")
    @mock.patch("os.symlink")
    def test2_extract_by_wine(self, mock_symlink, mock_unlink, mock_path_exists, mock_subprocess):
        """[scenario: install failed]"""
        mock_path_exists.return_value = True
        mock_subprocess().poll.return_value = 1
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        temp_dir = "/home/makson/.cache/minigalaxy/extract/1136126792"
        exp = "Wine extraction failed."
        obs = installer.extract_by_wine(game, installer_path, temp_dir)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    @mock.patch("os.path.isfile")
    def test1_postinstaller(self, mock_path_isfile, mock_subprocess):
        mock_path_isfile.return_value = False
        mock_subprocess().poll.return_value = 1
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift")
        exp = ""
        obs = installer.postinstaller(game)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    @mock.patch("os.path.isfile")
    @mock.patch("os.chmod")
    def test2_postinstaller(self, mock_chmod, mock_path_isfile, mock_subprocess):
        mock_path_isfile.return_value = True
        mock_subprocess().poll.return_value = 0
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift")
        exp = ""
        obs = installer.postinstaller(game)
        self.assertEqual(exp, obs)

    @mock.patch('subprocess.Popen')
    @mock.patch("os.path.isfile")
    @mock.patch("os.chmod")
    def test3_postinstaller(self, mock_chmod, mock_path_isfile, mock_subprocess):
        mock_path_isfile.return_value = True
        mock_subprocess().poll.return_value = 1
        mock_subprocess().stdout.readlines.return_value = ["stdout", "stderr"]
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift")
        exp = "Postinstallation script failed: /home/makson/GOG Games/Absolute Drift/support/postinst.sh"
        obs = installer.postinstaller(game)
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
    def test1_verify_disk_space(self, mock_os_statvfs):
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
        obs = installer.verify_disk_space(game, installer_file)
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
        mock_subprocess().communicate.return_value = [stdout, "stderr"]
        installer_path = "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        exp = 159236636
        obs = installer.get_game_size_from_unzip(installer_path)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.getsize')
    @mock.patch('os.listdir')
    @mock.patch('os.path.isdir')
    def test_compare_directory_true(self, mock_path_isdir, mock_list_dir, mock_os_path_getsize):
        mock_path_isdir.return_value = True
        mock_list_dir.return_value = ["beneath_a_steel_sky_en_gog_2_20150.sh", "beneath_a_steel_sky_en_gog_2_20150.part1"]
        mock_os_path_getsize.return_value = 100

        obs = installer.compare_directories("/home/test/.cache/minigalaxy/installer/test", "/home/test/GOG Games/installer/test")
        self.assertEqual(obs, True)

    @mock.patch('os.path.getsize')
    @mock.patch('os.listdir')
    @mock.patch('os.path.isdir')
    def test_compare_directory_false(self, mock_path_isdir, mock_list_dir, mock_os_path_getsize):
        mock_path_isdir.return_value = True
        mock_list_dir.side_effect = [
            ["beneath_a_steel_sky_en_gog_2_20150.sh", "beneath_a_steel_sky_en_gog_2_20150.part1"],
            ["beneath_a_steel_sky_en_gog_2_20150.sh"],
        ]

        obs = installer.compare_directories("/home/test/.cache/minigalaxy/installer/test", "/home/test/GOG Games/installer/test")
        self.assertEqual(obs, False)

        mock_list_dir.side_effect = [
            ["beneath_a_steel_sky_en_gog_2_20150.sh", "beneath_a_steel_sky_en_gog_2_20150.part1"],
            ["beneath_a_steel_sky_en_gog_2_20150.sh", "beneath_a_steel_sky_en_gog_2_20150.part1"],
        ]
        mock_os_path_getsize.side_effect = [100, 200, 300, 400]

        obs = installer.compare_directories("/home/test/.cache/minigalaxy/installer/test", "/home/test/GOG Games/installer/test")
        self.assertEqual(obs, False)

    def test_remove_installer_no_installer(self):
        """
        No installer present
        """
        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath a Steel Sky", platform="linux")
        installer_path = "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/this/is/a/fake/directory", False)
        exp = "No installer directory is present: /home/i/.cache/minigalaxy/download/Beneath a Steel Sky"
        self.assertEqual(obs, exp)

    @mock.patch('os.path.isdir')
    @mock.patch('minigalaxy.installer.compare_directories')
    @mock.patch('shutil.rmtree')
    @mock.patch('os.remove')
    @mock.patch('os.listdir')
    def test_remove_installer_no_keep(self, mock_list_dir, mock_os_remove, mock_shutil_rmtree, mock_compare_directories, mock_os_path_isdir):
        """
        Disabled keep_installer
        """
        mock_os_path_isdir.return_value = True
        mock_compare_directories.return_value = False
        mock_list_dir.return_value = ["beneath_a_steel_sky_en_gog_2_20150.sh"]

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath a Steel Sky", platform="linux")
        installer_path = "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/some/directory/test", False)
        assert mock_os_remove.called
        assert not mock_shutil_rmtree.called
        self.assertEqual(obs, "")

    @mock.patch('os.remove')
    @mock.patch('shutil.rmtree')
    @mock.patch('minigalaxy.installer.compare_directories')
    @mock.patch('os.path.isdir')
    def test_remove_installer_same_content(self, mock_os_path_isdir, mock_compare_directories, mock_shutil_rmtree, mock_os_remove):
        """
        Same content of installer and keep dir
        """
        mock_os_path_isdir.return_value = True
        mock_compare_directories.return_value = True

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath a Steel Sky", platform="linux")
        installer_path = "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/home/i/GOG Games/installer", True)
        assert not mock_shutil_rmtree.called
        assert not mock_os_remove.called
        self.assertEqual(obs, "")

    @mock.patch('os.remove')
    @mock.patch('shutil.move')
    @mock.patch('shutil.rmtree')
    @mock.patch('minigalaxy.installer.compare_directories')
    @mock.patch('os.path.isdir')
    def test_remove_installer_keep(self, mock_os_path_isdir, mock_compare_directories, mock_shutil_rmtree, mock_shutil_move, mock_os_remove):
        """
        Keep installer dir
        """
        mock_os_path_isdir.return_value = True
        mock_compare_directories.return_value = False

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath a Steel Sky", platform="linux")
        installer_path = "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/home/i/GOG Games/installer", True)
        assert mock_shutil_rmtree.called
        assert mock_shutil_move.called
        assert not mock_os_remove.called
        self.assertEqual(obs, "")

    @patch("os.listdir")
    @mock.patch('os.remove')
    @mock.patch('shutil.move')
    @mock.patch('shutil.rmtree')
    @mock.patch('minigalaxy.installer.compare_directories')
    @mock.patch('os.path.isdir')
    def test_remove_installer_from_keep(self, mock_os_path_isdir, mock_compare_directories, mock_shutil_rmtree, mock_shutil_move, mock_os_remove, mock_os_listdir):
        """
        Called from keep dir
        """
        mock_os_path_isdir.return_value = True
        mock_compare_directories.return_value = False
        mock_os_listdir.return_value = []

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath A Steel Sky", platform="linux")
        installer_path = "/home/i/GOG Games/installer/Beneath A Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/home/i/GOG Games/installer", False)
        assert not mock_shutil_rmtree.called
        assert not mock_shutil_move.called
        assert not mock_os_remove.called
        self.assertEqual(obs, "")
