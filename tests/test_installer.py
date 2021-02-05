import sys
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch, mock_open

m_config = MagicMock()
sys.modules['minigalaxy.config'] = m_config
from minigalaxy.game import Game
from minigalaxy import installer
from minigalaxy.translation import _


class Test(TestCase):
    @mock.patch('os.path.exists')
    @mock.patch('hashlib.md5')
    def test1_verify_installer_integrity(self, mock_hash, mock_is_file):
        md5_sum = "5cc68247b61ba31e37e842fd04409d98"
        mock_is_file.return_value = True
        mock_hash().hexdigest.return_value = md5_sum
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky",
                    md5sum=md5_sum)
        installer_path = "/home/user/.cache/minigalaxy/download/" \
                         "Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        exp = ""
        with patch("builtins.open", mock_open(read_data=b"")):
            obs = installer.verify_installer_integrity(game, installer_path)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('hashlib.md5')
    def test2_verify_installer_integrity(self, mock_hash, mock_is_file):
        md5_sum = "5cc68247b61ba31e37e842fd04409d98"
        corrupted_md5_sum = "99999947b61ba31e37e842fd04409d98"
        mock_is_file.return_value = True
        mock_hash().hexdigest.return_value = corrupted_md5_sum
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky",
                    md5sum=md5_sum)
        installer_path = "/home/user/.cache/minigalaxy/download/" \
                         "Beneath a Steel Sky/beneath_a_steel_sky_en_gog_2_20150.sh"
        exp = _("{} was corrupted. Please download it again.").format(installer_path)
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


del sys.modules["minigalaxy.config"]
del sys.modules["minigalaxy.game"]
