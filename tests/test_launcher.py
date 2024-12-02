import subprocess
from unittest import TestCase, mock
from unittest.mock import MagicMock, mock_open

from minigalaxy import launcher
from minigalaxy.game import Game


class Test(TestCase):
    def test1_determine_launcher_type(self):
        files = ['thumbnail.jpg', 'docs', 'support', 'game', 'start.sh', 'minigalaxy-dlc.json', 'gameinfo']
        exp = "start_script"
        obs = launcher.determine_launcher_type(files)
        self.assertEqual(exp, obs)

    @mock.patch('shutil.which')
    def test2_determine_launcher_type(self, mock_shutil_which):
        mock_shutil_which.return_value = True
        files = ['thumbnail.jpg', 'data', 'docs', 'support', 'beneath.ini', 'scummvm', 'start.sh', 'gameinfo']
        exp = "scummvm"
        obs = launcher.determine_launcher_type(files)
        self.assertEqual(exp, obs)

    def test3_determine_launcher_type(self):
        files = ['thumbnail.jpg', 'docs', 'support', 'unins000.exe', 'minigalaxy-dlc.json', 'gameinfo']
        exp = "windows"
        obs = launcher.determine_launcher_type(files)
        self.assertEqual(exp, obs)

    @mock.patch('shutil.which')
    def test4_determine_launcher_type(self, mock_shutil_which):
        mock_shutil_which.return_value = True
        files = ['thumbnail.jpg', 'docs', 'support', 'dosbox', 'minigalaxy-dlc.json', 'gameinfo']
        exp = "dosbox"
        obs = launcher.determine_launcher_type(files)
        self.assertEqual(exp, obs)

    def test5_determine_launcher_type(self):
        files = ['thumbnail.jpg', 'docs', 'support', 'game', 'minigalaxy-dlc.json', 'gameinfo']
        exp = "final_resort"
        obs = launcher.determine_launcher_type(files)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('glob.glob')
    def test1_get_windows_exe_cmd(self, mock_glob, mock_exists):
        mock_glob.return_value = ["/test/install/dir/start.exe", "/test/install/dir/unins000.exe"]
        mock_exists.return_value = True
        files = ['thumbnail.jpg', 'docs', 'support', 'game', 'minigalaxy-dlc.json', 'start.exe', 'unins000.exe']
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ["wine", "start.exe"]
        obs = launcher.get_windows_exe_cmd(game, files)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock_open, read_data="")
    @mock.patch('os.chdir')
    def test2_get_windows_exe_cmd(self, mock_os_chdir, mo, mock_exists):
        goggame_1414471894_info_content = """{
        "buildId": "53350324452482937",
        "clientId": "53185732904249211",
        "gameId": "1414471894",
        "language": "Russian",
        "languages": [
        "ru-RU"
        ],
        "name": "Metro Exodus - Sam's Story",
        "osBitness": [
        "64"
        ],
        "playTasks": [],
        "rootGameId": "1407287452",
        "version": 1
        }"""
        goggame_1407287452_info_content = """{
        "buildId": "53350324452482937",
        "clientId": "53185732904249211",
        "gameId": "1407287452",
        "language": "Russian",
        "languages": [
        "ru-RU"
        ],
        "name": "Metro Exodus",
        "osBitness": [
        "64"
        ],
        "playTasks": [
        {
        "category": "game",
        "isPrimary": true,
        "languages": [
        "ru-RU"
        ],
        "name": "Metro Exodus",
        "osBitness": [
        "64"
        ],
        "path": "MetroExodus.exe",
        "type": "FileTask"
        }
        ],
        "rootGameId": "1407287452",
        "version": 1
        }"""
        handlers = (mock_open(read_data=goggame_1414471894_info_content).return_value, mock_open(read_data=goggame_1407287452_info_content).return_value)
        mo.side_effect = handlers
        mock_exists.return_value = True
        files = ['thumbnail.jpg', 'docs', 'support', 'game', 'minigalaxy-dlc.json', 'MetroExodus.exe', 'unins000.exe',
                 'goggame-1407287452.info', 'goggame-1414471894.info']
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ['wine', 'start', '/b', '/wait', '/d', 'c:\\game\\.', 'c:\\game\\MetroExodus.exe']
        obs = launcher.get_windows_exe_cmd(game, files)
        self.assertEqual(exp, obs)

    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock_open, read_data="")
    @mock.patch('os.chdir')
    def test3_get_windows_exe_cmd(self, mock_os_chdir, mo, mock_exists):
        goggame_1207658919_info_content = """{
        "buildId": "52095557858882770",
        "clientId": "49843178982252086",
        "gameId": "1207658919",
        "language": "English",
        "languages": [
        "en-US"
        ],
        "name": "Rayman Forever",
        "playTasks": [
        {
        "arguments": "-conf \\"..\\\\dosboxRayman.conf\\" -conf \\"..\\\\dosboxRayman_single.conf\\" -noconsole -c \\"exit\\"",
        "category": "game",
        "isPrimary": true,
        "languages": [
            "*"
        ],
        "name": "Rayman Forever",
        "path": "DOSBOX\\\\dosbox.exe",
        "type": "FileTask",
        "workingDir": "DOSBOX"
        },
        {
        "arguments": "1207658919",
        "category": "tool",
        "languages": [
            "*"
        ],
        "name": "Graphic Mode Setup",
        "path": "DOSBOX\\\\GOGDOSConfig.exe",
        "type": "FileTask",
        "workingDir": "DOSBOX"
        },
        {
        "category": "document",
        "languages": [
            "*"
        ],
        "link": "http://www.gog.com/support/rayman_forever",
        "name": "Support",
        "type": "URLTask"
        },
        {
        "category": "document",
        "languages": [
            "*"
        ],
        "name": "Manual",
        "path": "Manual.pdf",
        "type": "FileTask"
        },
        {
        "category": "tool",
        "languages": [
            "*"
        ],
        "name": "Mapper",
        "path": "RayKit\\\\Mapper.exe",
        "type": "FileTask",
        "workingDir": "RayKit"
        }
        ],
        "rootGameId": "1207658919",
        "version": 1
        }"""
        mo.side_effect = (mock_open(read_data=goggame_1207658919_info_content).return_value,)
        mock_exists.return_value = True
        files = ['goggame-1207658919.script', 'DOSBOX', 'thumbnail.jpg', 'game.gog', 'unins000.dat', 'webcache.zip',
                 'EULA.txt', 'Music', 'dosboxRayman_single.conf', 'Rayman', 'unins000.exe', 'support.ico', 'prefix',
                 'goggame-1207658919.info', 'Manual.pdf', 'gog.ico', 'unins000.msg', 'goggame-1207658919.hashdb',
                 'RayFan', 'dosboxRayman.conf', 'unins000.ini', 'thumbnail_100.jpg', 'RayKit', 'game.ins',
                 'goggame-1207658919.ico', 'goglog.ini', 'Launch Rayman Forever.lnk', 'cloud_saves',
                 'thumbnail_196.jpg']
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ['wine', 'start', '/b', '/wait', '/d', 'c:\\game\\DOSBOX', 'c:\\game\\DOSBOX\\dosbox.exe', '-conf', '"..\\dosboxRayman.conf"',
               '-conf', '"..\\dosboxRayman_single.conf"', '-noconsole', '-c', '"exit"']
        obs = launcher.get_windows_exe_cmd(game, files)
        self.assertEqual(exp, obs)

    def test_get_dosbox_exe_cmd(self):
        files = ['thumbnail.jpg', 'docs', 'support', 'dosbox_bbb_single.conf', 'dosbox_aaa.conf', 'dosbox']
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ["dosbox", "-conf", "dosbox_aaa.conf", "-conf", "dosbox_bbb_single.conf", "-no-console", "-c", "exit"]
        obs = launcher.get_dosbox_exe_cmd(game, files)
        self.assertEqual(exp, obs)

    def test_get_scummvm_exe_cmd(self):
        files = ['thumbnail.jpg', 'data', 'docs', 'support', 'beneath.ini', 'scummvm', 'start.sh', 'gameinfo']
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ["scummvm", "-c", "beneath.ini"]
        obs = launcher.get_scummvm_exe_cmd(game, files)
        self.assertEqual(exp, obs)

    def test_get_start_script_exe_cmd(self):
        exp = ["./start.sh"]
        obs = launcher.get_start_script_exe_cmd()
        self.assertEqual(exp, obs)

    @mock.patch('os.getcwd')
    @mock.patch('os.chdir')
    @mock.patch('subprocess.Popen')
    @mock.patch('minigalaxy.launcher.get_execute_command')
    def test1_run_game_subprocess(self, launcher_mock, mock_popen, mock_os_chdir, mock_os_getcwd):
        mock_process = "Mock Process"
        mock_popen.return_value = mock_process
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ("", mock_process)
        obs = launcher.run_game_subprocess(game)
        self.assertEqual(exp, obs)

    @mock.patch('os.getcwd')
    @mock.patch('os.chdir')
    @mock.patch('subprocess.Popen')
    @mock.patch('minigalaxy.launcher.get_execute_command')
    def test2_run_game_subprocess(self, launcher_mock, mock_popen, mock_os_chdir, mock_os_getcwd):
        mock_popen.side_effect = FileNotFoundError()
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ('No executable was found in /test/install/dir', None)
        obs = launcher.run_game_subprocess(game)
        self.assertEqual(exp, obs)

    @mock.patch('minigalaxy.launcher.check_if_game_start_process_spawned_final_process')
    def test1_check_if_game_started_correctly(self, mock_check_game):
        mock_process = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 1)
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = ""
        obs = launcher.check_if_game_started_correctly(mock_process, game)
        self.assertEqual(exp, obs)

    @mock.patch('minigalaxy.launcher.check_if_game_start_process_spawned_final_process')
    def test2_check_if_game_started_correctly(self, mock_check_game):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"Output message", None)
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = "Output message"
        obs = launcher.check_if_game_started_correctly(mock_process, game)
        self.assertEqual(exp, obs)

    @mock.patch('os.getpid')
    @mock.patch('subprocess.check_output')
    def test1_check_if_game_start_process_spawned_final_process(self, mock_check_output, mock_getpid):
        mock_check_output.return_value = b"""UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 lis24 ?        00:00:02 /sbin/init splash
root         2     0  0 lis24 ?        00:00:00 [kthreadd]
root         3     2  0 lis24 ?        00:00:00 [rcu_gp]
root         4     2  0 lis24 ?        00:00:00 [rcu_par_gp]
root         6     2  0 lis24 ?        00:00:00 [kworker/0:0H-kblockd]
"""
        mock_getpid.return_value = 1000
        err_msg = "Error Message"
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = err_msg
        obs = launcher.check_if_game_start_process_spawned_final_process(err_msg, game)
        self.assertEqual(exp, obs)

    @mock.patch('os.getpid')
    @mock.patch('subprocess.check_output')
    def test2_check_if_game_start_process_spawned_final_process(self, mock_check_output, mock_getpid):
        mock_check_output.return_value = b"""UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 lis24 ?        00:00:02 /sbin/init splash
root         2     0  0 lis24 ?        00:00:00 [kthreadd]
root         3     2  0 lis24 ?        00:00:00 [rcu_gp]
root         4     2  0 lis24 ?        00:00:00 [rcu_par_gp]
root         6     2  0 lis24 ?        00:00:00 [kworker/0:0H-kblockd]
makson    1006     2  0 lis24 ?        00:00:00 /bin/sh /home/makson/.paradoxlauncher/launcher-v2.2020.15/Paradox Launcher --pdxlGameDir /home/makson/GOG Games/Stellaris/game --gameDir /home/makson/GOG Games/Stellaris/game
"""
        mock_getpid.return_value = 1000
        err_msg = "Error Message"
        game = Game("Stellaris", install_dir="/home/makson/GOG Games")
        exp = ""
        obs = launcher.check_if_game_start_process_spawned_final_process(err_msg, game)
        self.assertEqual(exp, obs)

    @mock.patch('os.getpid')
    @mock.patch('subprocess.check_output')
    def test3_check_if_game_start_process_spawned_final_process(self, mock_check_output, mock_getpid):
        mock_check_output.return_value = b"""UID        PID  PPID  C STIME TTY          TIME CMD
root     12486     2  0 17:47 ?        00:00:00 [kworker/u17:3-kcryptd]
root     12543     2  0 17:53 ?        00:00:00 [kworker/u17:1-kcryptd]
root     12617     2  0 18:02 ?        00:00:00 [kworker/5:1-ata_sff]
root     12652     2  0 18:07 ?        00:00:00 [kworker/0:0-events]
root     12682     2  0 18:08 ?        00:00:00 [kworker/5:2-ata_sff]
root     12699     2  0 18:08 ?        00:00:00 [kworker/u17:0-kcryptd]
makson   12783  6690  1 18:09 pts/4    00:00:01 /usr/bin/python3 build/scripts-3.7/minigalaxy
makson   12866  1378  0 18:09 pts/4    00:00:00 /bin/sh /home/makson/.paradoxlauncher/launcher-v2.2021.1/Paradox Launcher --pdxlGameDir /home/makson/GOG Games/Imperator Rome/game/launcher --gameDir /home/makson/GOG Games/Imperator Rome/game/launcher
"""
        mock_getpid.return_value = 1000
        err_msg = "Error Message"
        game = Game("Imperator: Rome", install_dir="/home/makson/GOG Games")
        exp = ""
        obs = launcher.check_if_game_start_process_spawned_final_process(err_msg, game)
        self.assertEqual(exp, obs)
