import subprocess
from unittest import TestCase, mock
from unittest.mock import MagicMock, mock_open

from minigalaxy import launcher
from minigalaxy.game import Game, InfoKey
from minigalaxy.launch_command import LaunchCommand


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

    @mock.patch("minigalaxy.launcher.get_wine_path")
    @mock.patch("minigalaxy.launcher.wine_restore_game_link", MagicMock)
    def test1_get_windows_launch_commands(self, mock_get_wine_path: MagicMock):
        mock_get_wine_path.return_value = "/usr/bin/wine"
        files = [
            "thumbnail.jpg",
            "docs",
            "support",
            "game",
            "minigalaxy-dlc.json",
            "unins000.exe",
            "UnityCrashHandler64.exe",
            "nglide_config.exe",
            "ipxconfig.exe",
            "BNUpdate.exe",
            "VidSize.exe",
            "FRED2.exe",
            "FS2.exe",
            "start.exe",
        ]
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = [
            LaunchCommand(
                name="nglide_config.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/nglide_config.exe"]
            ),
            LaunchCommand(
                name="ipxconfig.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/ipxconfig.exe"]
            ),
            LaunchCommand(
                name="BNUpdate.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/BNUpdate.exe"]
            ),
            LaunchCommand(
                name="VidSize.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/VidSize.exe"]
            ),
            LaunchCommand(
                name="FRED2.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/FRED2.exe"]
            ),
            LaunchCommand(
                name="FS2.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/FS2.exe"]
            ),
            LaunchCommand(
                name="start.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/start.exe"]
            ),
        ]
        obs = launcher.get_windows_launch_commands(game, files)
        self.assertEqual(exp, obs)

    @mock.patch("minigalaxy.launcher.get_wine_path")
    @mock.patch("minigalaxy.launcher.wine_restore_game_link", MagicMock)
    def test1_get_windows_launch_commands_can_choose_lnk(self, mock_get_wine_path: MagicMock):
        mock_get_wine_path.return_value = "/usr/bin/wine"
        files = [
            "thumbnail.jpg",
            "docs",
            "support",
            "game",
            "minigalaxy-dlc.json",
            "unins000.exe",
            "UnityCrashHandler64.exe",
            "start.lnk",
            "start.exe",
        ]
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = [
            LaunchCommand(
                name="start.lnk",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/start.lnk"]
            ),
            LaunchCommand(
                name="start.exe",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', "/usr/bin/wine", "/test/install/dir/start.exe"]
            )
        ]
        obs = launcher.get_windows_launch_commands(game, files)
        self.assertEqual(exp, obs)

    @mock.patch("minigalaxy.launcher.get_wine_path")
    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock_open, read_data="")
    @mock.patch('os.chdir')
    @mock.patch("minigalaxy.launcher.wine_restore_game_link", MagicMock)
    def test2_get_windows_launch_commands(self, mock_os_chdir, mo, mock_exists, mock_get_wine_path):
        mock_get_wine_path.return_value = "wine"
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

        def open_file(filename, mode):
            if filename.endswith("goggame-1414471894.info"):
                return mock_open(read_data=goggame_1414471894_info_content).return_value
            elif filename.endswith("goggame-1407287452.info"):
                return mock_open(read_data=goggame_1407287452_info_content).return_value
            else:
                print('open called with '+filename)
                pass
        mo.side_effect = open_file
        mock_exists.return_value = True
        files = ['thumbnail.jpg', 'docs', 'support', 'game', 'minigalaxy-dlc.json', 'MetroExodus.exe', 'unins000.exe',
                 'goggame-1407287452.info', 'goggame-1414471894.info']
        game = Game("Test Game", install_dir="/test/install/dir", game_id=1407287452)
        exp = [
            LaunchCommand(
                name="goginfo",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix', 'wine', 'start', '/b', '/wait', '/d', 'c:\\game\\.',
                         'c:\\game\\MetroExodus.exe']
            )
        ]
        obs = launcher.get_windows_launch_commands(game, files)
        self.assertEqual(exp, obs)

    @mock.patch("minigalaxy.launcher.get_wine_path")
    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock_open, read_data="")
    @mock.patch('os.chdir')
    @mock.patch("minigalaxy.launcher.wine_restore_game_link", MagicMock)
    def test3_get_windows_launch_commands(self, mock_os_chdir, mo, mock_exists, mock_wine_path):
        mock_wine_path.return_value = "wine"
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
        exp = [
            LaunchCommand(
                name="goginfo",
                command=['env', 'WINEPREFIX=/test/install/dir/prefix',
                         'wine', 'start', '/b', '/wait', '/d', 'c:\\game\\DOSBOX',
                         'c:\\game\\DOSBOX\\dosbox.exe', '-conf', '..\\dosboxRayman.conf',
                         '-conf', '..\\dosboxRayman_single.conf', '-noconsole', '-c', 'exit']
            )
        ]
        obs = launcher.get_windows_launch_commands(game, files)
        self.assertEqual(exp, obs)

    def test_get_dosbox_launch_commands(self):
        files = ['thumbnail.jpg', 'docs', 'support', 'dosbox_bbb_single.conf', 'dosbox_aaa.conf', 'dosbox']
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = [
            LaunchCommand(
                name="dosbox",
                command=["dosbox", "-conf", "dosbox_aaa.conf", "-conf", "dosbox_bbb_single.conf", "-no-console", "-c", "exit"]
            )
        ]
        obs = launcher.get_dosbox_launch_commands(game, files)
        self.assertEqual(exp, obs)

    def test_get_scummvm_launch_commands(self):
        files = ['thumbnail.jpg', 'data', 'docs', 'support', 'beneath.ini', 'scummvm', 'start.sh', 'gameinfo']
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = [
            LaunchCommand(
                name="scummvm",
                command=["scummvm", "-c", "beneath.ini"]
            )
        ]
        obs = launcher.get_scummvm_launch_commands(game, files)
        self.assertEqual(exp, obs)

    def test_get_start_script_launch_commands(self):
        game = Game("Test Game", install_dir="/test/install/dir")
        exp = [
            LaunchCommand(
                name="start.sh",
                command=["/test/install/dir/start.sh"]
            )
        ]
        obs = launcher.get_start_script_launch_commands(game)
        self.assertEqual(exp, obs)

    @mock.patch('os.getcwd')
    @mock.patch('os.chdir')
    @mock.patch('subprocess.Popen')
    def test1_run_game_subprocess(self, mock_popen, mock_os_chdir, mock_os_getcwd):
        mock_process = "Mock Process"
        mock_popen.return_value = mock_process
        game = Game("Test Game", install_dir="/test/install/dir")
        launch_command = LaunchCommand(
            name="test",
            command=["/test/install/dir/start.sh"]
        )
        exp = ("", mock_process)
        obs = launcher.run_game_subprocess(game, launch_command=launch_command)
        self.assertEqual(exp, obs)

    @mock.patch('os.getcwd')
    @mock.patch('os.chdir')
    @mock.patch('subprocess.Popen')
    def test2_run_game_subprocess(self, mock_popen, mock_os_chdir, mock_os_getcwd):
        mock_popen.side_effect = FileNotFoundError()
        game = Game("Test Game", install_dir="/test/install/dir")
        launch_command = LaunchCommand(
            name="test",
            command=["/test/install/dir/start.sh"]
        )
        exp = ('No executable test was found in /test/install/dir', None)
        obs = launcher.run_game_subprocess(game, launch_command=launch_command)
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

    def test_get_windows_environment_defaults_to_wine(self):
        game = Game("Test Game", install_dir="/test/install/dir")

        with mock.patch.object(game, "get_info", return_value=""):
            observed = launcher.get_windows_environment(game)

        expected = [
            "WINEPREFIX=/test/install/dir/prefix",
        ]

        self.assertEqual(expected, observed)

    def test_get_windows_environment_proton(self):
        game = Game("Test Game", install_dir="/test/install/dir")

        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(key, default_value),
        ):
            observed = launcher.get_windows_environment(game)

        expected = [
            "WINEPREFIX=/test/install/dir/prefix",
            "PROTONPATH=/steam/Proton - Experimental",
            "STORE=gog",
            "GAMEID=0",
        ]

        self.assertEqual(expected, observed)

    def test_get_windows_runner_uses_umu_for_proton(self):
        game = Game("Test Game", install_dir="/test/install/dir")

        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(key, default_value),
        ), mock.patch(
            "minigalaxy.launcher.shutil.which",
            return_value="/usr/bin/umu-run",
        ):
            observed = launcher.get_windows_runner(game)

        self.assertEqual("/usr/bin/umu-run", observed)

    def test_get_windows_launch_commands_proton(self):
        files = [
            "unins000.exe",
            "start.exe",
        ]

        game = Game("Test Game", install_dir="/test/install/dir")

        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(key, default_value),
        ), mock.patch(
            "minigalaxy.launcher.shutil.which",
            return_value="/usr/bin/umu-run",
        ), mock.patch(
            "minigalaxy.launcher.wine_restore_game_link"
        ):
            observed = launcher.get_windows_launch_commands(game, files)

        expected = [
            LaunchCommand(
                name="start.exe",
                command=[
                    "env",
                    "WINEPREFIX=/test/install/dir/prefix",
                    "PROTONPATH=/steam/Proton - Experimental",
                    "STORE=gog",
                    "GAMEID=0",
                    "/usr/bin/umu-run",
                    "/test/install/dir/start.exe",
                ],
            )
        ]

        self.assertEqual(expected, observed)

    def test_get_windows_exe_cmd_from_goggame_info_proton(self):
        game = Game("Test Game", install_dir="/test/install/dir")

        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }

        goggame_info = """{
            "playTasks": [
                {
                    "isPrimary": true,
                    "workingDir": "bin",
                    "path": "game.exe",
                    "arguments": "--foo bar"
                }
            ]
        }"""

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(key, default_value),
        ), mock.patch(
            "minigalaxy.launcher.shutil.which",
            return_value="/usr/bin/umu-run",
        ), mock.patch(
            "minigalaxy.launcher.os.chdir"
        ), mock.patch(
            "builtins.open",
            mock_open(read_data=goggame_info),
        ):
            observed = launcher.get_windows_exe_cmd_from_goggame_info(
                game,
                "/test/install/dir/goggame-0.info",
            )

        expected = [
            "/usr/bin/umu-run",
            "start",
            "/b",
            "/wait",
            "/d",
            "c:\\game\\bin",
            "c:\\game\\game.exe",
            "--foo",
            "bar",
        ]

        self.assertEqual(expected, observed)

    def test_uses_proton_even_when_proton_path_is_empty(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(
                key,
                default_value,
            ),
        ):
            self.assertTrue(launcher.uses_proton(game))

    def test_get_windows_runner_proton_never_calls_wine(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(
                key,
                default_value,
            ),
        ), mock.patch(
            "minigalaxy.launcher.find_umu_run",
            return_value="/home/test/.local/bin/umu-run",
        ), mock.patch(
            "minigalaxy.launcher.get_wine_path",
        ) as mock_get_wine_path:
            observed = launcher.get_windows_runner(game)

        self.assertEqual(
            "/home/test/.local/bin/umu-run",
            observed,
        )
        mock_get_wine_path.assert_not_called()

    def test_validate_proton_requires_configured_path(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(
                key,
                default_value,
            ),
        ):
            observed = launcher.validate_windows_compatibility(game)

        self.assertEqual(
            "Proton is selected for this game, but no Proton "
            "compatibility tool is configured.",
            observed,
        )

    def test_validate_proton_requires_selected_tool(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Missing Proton",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(
                key,
                default_value,
            ),
        ), mock.patch(
            "minigalaxy.launcher.os.path.isfile",
            return_value=False,
        ):
            observed = launcher.validate_windows_compatibility(game)

        self.assertEqual(
            "The selected Proton compatibility tool is unavailable: "
            "/steam/Missing Proton",
            observed,
        )

    def test_validate_proton_requires_umu(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(
                key,
                default_value,
            ),
        ), mock.patch(
            "minigalaxy.launcher.os.path.isfile",
            return_value=True,
        ), mock.patch(
            "minigalaxy.launcher.find_umu_run",
            return_value="",
        ), mock.patch(
            "minigalaxy.launcher.get_umu_status",
            return_value=None,
        ):
            observed = launcher.validate_windows_compatibility(game)

        self.assertEqual(
            "UMU Launcher (umu-run) version 1.4.4 or newer is required to "
            "install and run games with Proton through the Steam Linux Runtime, "
            "but it was not found.",
            observed,
        )

    def test_find_umu_run_uses_compatible_discovered_umu(self):
        installation = MagicMock()
        installation.path = "/home/test/.local/bin/umu-run"

        with mock.patch(
            "minigalaxy.launcher.find_compatible_umu",
            return_value=installation,
        ):
            observed = launcher.find_umu_run()

        self.assertEqual(
            "/home/test/.local/bin/umu-run",
            observed,
        )

    def test_validate_proton_rejects_old_umu_version(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }
        status = MagicMock()
        status.version_text = "1.4.3"

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(
                key,
                default_value,
            ),
        ), mock.patch(
            "minigalaxy.launcher.os.path.isfile",
            return_value=True,
        ), mock.patch(
            "minigalaxy.launcher.find_umu_run",
            return_value="",
        ), mock.patch(
            "minigalaxy.launcher.get_umu_status",
            return_value=status,
        ):
            observed = launcher.validate_windows_compatibility(game)

        self.assertEqual(
            "UMU Launcher 1.4.3 is installed, but version 1.4.4 or newer "
            "is required for Proton support.",
            observed,
        )

    def test_config_game_proton_uses_runinprefix(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        values = {
            InfoKey.WINDOWS_RUNNER: "proton",
            InfoKey.PROTON_PATH: "/steam/Proton - Experimental",
        }

        with mock.patch.object(
            game,
            "get_info",
            side_effect=lambda key, default_value="": values.get(
                key,
                default_value,
            ),
        ), mock.patch(
            "minigalaxy.launcher.validate_windows_compatibility",
            return_value="",
        ), mock.patch(
            "minigalaxy.launcher.find_umu_run",
            return_value="/usr/bin/umu-run",
        ), mock.patch(
            "minigalaxy.launcher.subprocess.Popen",
        ) as mock_popen:
            observed = launcher.config_game(game)

        self.assertEqual("", observed)
        mock_popen.assert_called_once_with([
            "env",
            "WINEPREFIX=/test/install/dir/prefix",
            "PROTONPATH=/steam/Proton - Experimental",
            "STORE=gog",
            "GAMEID=0",
            "PROTON_VERB=runinprefix",
            "/usr/bin/umu-run",
            "winecfg",
        ])

    def test_start_game_returns_proton_validation_error_before_spawn(self):
        game = Game(
            "Test Game",
            install_dir="/test/install/dir",
            platform="windows",
        )
        command = LaunchCommand(
            name="game.exe",
            command=["umu-run", "game.exe"],
        )
        expected = "UMU Launcher is required."

        with mock.patch(
            "minigalaxy.launcher.validate_windows_compatibility",
            return_value=expected,
        ), mock.patch(
            "minigalaxy.launcher.run_game_subprocess",
        ) as mock_run:
            observed = launcher.start_game(game, command)

        self.assertEqual(expected, observed)
        mock_run.assert_not_called()
