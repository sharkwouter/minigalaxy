import copy
from unittest import TestCase, mock
from unittest.mock import patch, mock_open, MagicMock

from minigalaxy.game import Game
from minigalaxy import installer
from minigalaxy.translation import _
import minigalaxy


class Test(TestCase):
    @mock.patch('os.path.exists')
    def test_install_game(self, mock_exists):
        """[scenario: unhandled error]"""
        mock_exists.side_effect = FileNotFoundError("Testing unhandled errors during install")
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
        obs, use_temp = installer.extract_installer(game, installer_path, temp_dir, "en")
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
        obs, use_temp = installer.extract_installer(game, installer_path, temp_dir, "en")
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
        obs, temp_used = installer.extract_linux(installer_path, temp_dir)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('minigalaxy.installer.extract_by_wine')
    @mock.patch('shutil.which')
    def test1_get_lang_with_innoextract(self, mock_which, mock_wine_extract, mock_exists):
        """[scenario: no innoextract - default en-US used]"""
        mock_which.return_value = False
        mock_exists.return_value = True
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        exp = "en-US"
        # check that lang passed to the wine installer is set up correctly
        mock_wine_extract.side_effect = lambda game, installer, lang: self.assertEqual(exp, lang)
        installer.extract_windows(game, installer_path, "en")

    @mock.patch('shutil.which')
    @mock.patch('minigalaxy.installer._exe_cmd')
    def test2_get_lang_with_innoextract(self, mock_exe, mock_which):
        """[scenario: innoextract --list-languages returns locale ids]"""
        lines = [" - fr-FR\n", " - jp-JP\n", " - en-US\n", " - ru-RU"]
        mock_exe.return_value = ''.join(lines), '', 0
        mock_which.return_value = '/bin/innoextract'
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        exp = "jp-JP"
        obs = installer.match_game_lang_to_installer(installer_path, "jp")
        self.assertEqual(exp, obs)

    @mock.patch('shutil.which')
    @mock.patch('minigalaxy.installer._exe_cmd')
    def test3_get_lang_with_innoextract(self, mock_exe, mock_which):
        """[scenario: innoextract --list-languages returns language names]"""
        lines = [" - english: English\n", " - german: Deutsch\n", " - french: Français"]
        mock_exe.return_value = ''.join(lines), '', 0
        mock_which.return_value = '/bin/innoextract'
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        exp = "french"
        obs = installer.match_game_lang_to_installer(installer_path, "fr")
        self.assertEqual(exp, obs)

    @mock.patch('shutil.which')
    @mock.patch('minigalaxy.installer._exe_cmd')
    def test4_get_lang_with_innoextract(self, mock_exe, mock_which):
        """[scenario: innoextract --list-languages can't be matched - default en-US is used]"""
        mock_exe.return_value = '', '', 0
        mock_which.return_value = '/bin/innoextract'
        installer_path = "/home/makson/.cache/minigalaxy/download/Absolute Drift/setup_absolute_drift_1.0f_(64bit)_(47863).exe"
        exp = "en-US"
        obs = installer.match_game_lang_to_installer(installer_path, "en")
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

    @mock.patch('shutil.which')
    @mock.patch('os.listdir')
    def test_get_exec_line(self, mock_list_dir, mock_which):
        mock_which.return_value = True

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath a Steel Sky", platform="linux")
        mock_list_dir.return_value = ["data", "docs", "scummvm", "support", "beneath.ini", "gameinfo", "start.sh"]

        result1 = installer.get_exec_line(game1)
        self.assertEqual("scummvm -c beneath.ini", result1)

        game2 = Game("Blocks That Matter", install_dir="/home/test/GOG Games/Blocks That Matter", platform="linux")
        mock_list_dir.return_value = ["data", "docs", "support", "gameinfo", "start.sh"]

        result2 = installer.get_exec_line(game2)
        self.assertEqual('"/home/test/GOG Games/Blocks That Matter/start.sh"', result2)

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

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.realpath")
    @mock.patch("minigalaxy.installer.is_empty_dir")
    @mock.patch('os.remove')
    @mock.patch("os.path.isfile")
    @mock.patch('os.rmdir')
    @mock.patch('os.listdir')
    def test_remove_installer_no_keep(self, mock_listdir, mock_rmdir, mock_isfile, mock_remove, mock_isempty, mock_realpath, mock_isdir):
        """Disabled keep_installer"""
        DL_DIR = "/home/i/.cache/minigalaxy/download"
        mock_realpath.side_effect = lambda p: DL_DIR if p == minigalaxy.paths.DOWNLOAD_DIR else p
        list_dir_returns = {
            "/home/i/.cache/minigalaxy": ["download", "icons"],
            DL_DIR: ["Beneath a Steel Sky"],
            "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky": ["beneath_a_steel_sky_en_gog_2_20150.sh"],
        }

        self.setup_os_mocks(list_dir_returns, mock_listdir, mock_rmdir, mock_isfile, mock_remove, mock_isempty, mock_isdir)

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath a Steel Sky", platform="linux")
        installer_path = "/home/i/.cache/minigalaxy/download/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/some/directory/test", False)

        assert mock_remove.called
        self.assertEqual(obs, "")

    @mock.patch("os.path.isdir")
    @mock.patch('os.remove')
    @mock.patch("os.path.isfile")
    @mock.patch('os.rmdir')
    @mock.patch('os.listdir')
    def test_remove_installer_keep(self, mock_listdir, mock_rmdir, mock_isfile, mock_remove, mock_isdir):
        """Keep installer dir"""

        list_dir_returns = {
            "/home/i/GOG Games/installer": ["Beneath a Steel Sky"],
            "/home/i/GOG Games/installer/Beneath a Steel Sky": ["beneath_a_steel_sky_en_gog_2_20150.sh"]
        }

        mock_listdir.side_effect = lambda path: list_dir_returns.get(path, [])
        mock_isfile.return_value = True
        mock_isdir.return_value = True

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath a Steel Sky", platform="linux")
        installer_path = "/home/i/GOG Games/installer/Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/home/i/GOG Games/installer", True)
        assert not mock_remove.called
        assert not mock_rmdir.called
        self.assertEqual(obs, "")

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.realpath")
    @mock.patch("minigalaxy.installer.is_empty_dir")
    @mock.patch('os.remove')
    @mock.patch("os.path.isfile")
    @mock.patch('os.rmdir')
    @mock.patch('os.listdir')
    def test_remove_installer_from_keep(self, mock_listdir, mock_rmdir, mock_isfile, mock_remove, mock_isempty, mock_realpath, mock_isdir):
        """ Called from keep dir"""

        DL_DIR = "/home/i/.cache/minigalaxy/download"
        mock_realpath.side_effect = lambda p: DL_DIR if p == minigalaxy.paths.DOWNLOAD_DIR else p
        list_dir_returns = {
            "/home/i/GOG Games": ["installer"],
            "/home/i/GOG Games/installer": ["Beneath A Steel Sky"],
            "/home/i/GOG Games/installer/Beneath A Steel Sky": []
        }

        self.setup_os_mocks(list_dir_returns, mock_listdir, mock_rmdir, mock_isfile, mock_remove, mock_isempty, mock_isdir)

        game1 = Game("Beneath A Steel Sky", install_dir="/home/test/GOG Games/Beneath A Steel Sky", platform="linux")
        installer_path = "/home/i/GOG Games/installer/Beneath A Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        obs = installer.remove_installer(game1, installer_path, "/home/i/GOG Games/installer", False)

        assert not mock_remove.called
        self.assertEqual(obs, "")

    def setup_os_mocks(self, file_structure, mock_listdir, mock_rmdir, mock_isfile, mock_remove, mock_isempty, mock_isdir):

        def rmdir_fake(path):
            if path in file_structure and len(file_structure[path]) == 0:
                # remove dir content listing itself
                del file_structure[path]
                # remove entry from parent list
                remove_fake(path)
            else:
                raise IOError("Directory not empty")

        def remove_fake(path):
            from os.path import dirname, basename
            filedir = dirname(path)
            filename = basename(path)
            if filedir in file_structure and filename in file_structure[filedir]:
                file_structure[filedir].remove(filename)
            else:
                raise FileNotFoundError(path)

        mock_isfile.side_effect = lambda path: path.endswith(".sh")
        mock_isdir.return_value = lambda path: path in file_structure
        mock_listdir.side_effect = lambda path: file_structure.get(path, [])
        mock_isempty.side_effect = lambda path: len(file_structure.get(path)) == 0
        mock_rmdir.side_effect = rmdir_fake
        mock_remove.side_effect = remove_fake
