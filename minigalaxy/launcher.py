import logging
import os
import subprocess
import shutil
import re
import json
import shlex
import threading
from typing import List

from minigalaxy.game import InfoKey
from minigalaxy.launch_command import LaunchCommand
from minigalaxy.translation import _
from minigalaxy.constants import BINARY_NAMES_TO_IGNORE


def get_wine_path(game):
    binary_name = "wine"
    custom_wine_path = game.get_info(InfoKey.CUSTOM_WINE)
    if custom_wine_path and custom_wine_path != shutil.which(binary_name):
        binary_name = custom_wine_path
    return binary_name


def uses_proton(game):
    """Return True when the game is configured to use a specific Proton build."""
    return (
        game.get_info(InfoKey.WINDOWS_RUNNER) == "proton"
        and bool(game.get_info(InfoKey.PROTON_PATH))
    )


def get_windows_runner(game):
    """
    Return the executable used to launch Windows programs for the game.

    Wine remains the default. When Proton is explicitly selected, UMU is used
    as the launcher and PROTONPATH selects the desired Proton installation.
    """
    if uses_proton(game):
        return shutil.which("umu-run") or "umu-run"

    return get_wine_path(game)


def get_windows_environment(game):
    """
    Return environment assignments required by the selected Windows runner.

    Keeping WINEPREFIX first preserves MiniGalaxy's existing Wine command
    layout exactly. Proton adds the variables required by UMU after it.
    """
    prefix = os.path.join(game.install_dir, "prefix")
    environment = [f"WINEPREFIX={prefix}"]

    if uses_proton(game):
        environment.extend([
            f"PROTONPATH={game.get_info(InfoKey.PROTON_PATH)}",
            "STORE=gog",
            "GAMEID=0",
        ])

    return environment


# should go into a separate file or into installer, but not possible ATM because
# it's a circular import otherwise
def wine_restore_game_link(game):
    game_dir = os.path.join(game.install_dir, 'prefix', 'dosdevices', 'c:', 'game')
    if not os.path.exists(game_dir):
        # 'game' directory itself does not count
        canonical_prefix = os.path.realpath(os.path.join(game_dir, '..'))
        relative = os.path.relpath(game.install_dir, canonical_prefix)
        os.symlink(relative, game_dir)


def config_game(game):
    subprocess.Popen(
        ['env', *get_windows_environment(game), get_windows_runner(game), 'winecfg']
    )


def regedit_game(game):
    subprocess.Popen(
        ['env', *get_windows_environment(game), get_windows_runner(game), 'regedit']
    )


def winetricks_game(game):
    prefix = os.path.join(game.install_dir, "prefix")
    subprocess.Popen(['env', f'WINEPREFIX={prefix}', 'winetricks'])


def start_game(game, execute_command: LaunchCommand) -> str:
    error_message = ""
    process = None
    if not execute_command:
        error_message = "Cannot launch game, because no command to execute was specified"
    if not error_message:
        error_message = set_fps_display(game)
    if not error_message:
        error_message, process = run_game_subprocess(game=game, launch_command=execute_command)
    if not error_message:
        error_message = check_if_game_started_correctly(process, game)
    if not error_message:
        send_game_output_to_stdout(process)
    if error_message:
        logging.error(_("Failed to start {}:").format(game.name), exc_info=1)
        logging.error("Cause of error: %s", error_message)
    return error_message


def get_execute_commands(game) -> list[LaunchCommand]:
    files = os.listdir(game.install_dir)
    launcher_type = determine_launcher_type(files)
    if launcher_type in ["start_script", "wine"]:
        launch_commands = get_start_script_launch_commands(game)
    elif launcher_type == "windows":
        launch_commands = get_windows_launch_commands(game, files)
    elif launcher_type == "dosbox":
        launch_commands = get_dosbox_launch_commands(game, files)
    elif launcher_type == "scummvm":
        launch_commands = get_scummvm_launch_commands(game, files)
    elif launcher_type == "final_resort":
        launch_commands = get_final_resort_launch_commands(game, files)
    else:
        # If no executable was found at all, raise an error
        raise FileNotFoundError()

    # Add additions to the launch command from the game config
    for launch_command in launch_commands:
        launch_command.apply_game_launch_config(game=game)

    logging.info("Launch commands for %s:", game.name)
    logging.info(f"{launch_commands}")
    for launch_command in launch_commands:
        logging.info("Launch commands for %s: %s", game.name, launch_command.name)

    return launch_commands


def determine_launcher_type(files):
    launcher_type = "unknown"
    if "unins000.exe" in files:
        launcher_type = "windows"
    elif "dosbox" in files and shutil.which("dosbox"):
        launcher_type = "dosbox"
    elif "scummvm" in files and shutil.which("scummvm"):
        launcher_type = "scummvm"
    elif "start.sh" in files:
        launcher_type = "start_script"
    elif "prefix" in files and shutil.which("wine"):
        launcher_type = "wine"
    elif "game" in files:
        launcher_type = "final_resort"
    return launcher_type


def get_windows_exe_cmd_from_goggame_info(game, file: str) -> List[str]:
    exe_cmd = []
    os.chdir(game.install_dir)
    with open(file, 'r') as info_file:
        info = json.loads(info_file.read())
        # if we have the workingDir property, start the executable at that directory
        for task in info.get("playTasks", []):
            if not task.get('isPrimary', False):
                continue

            if "path" in task:
                working_dir = task.get("workingDir", ".")
                path = task["path"]
                exe_cmd = [get_windows_runner(game), "start", "/b", "/wait",
                           "/d", f'c:\\game\\{working_dir}',
                           f'c:\\game\\{path}']
                if "arguments" in task:
                    exe_cmd += shlex.split(task["arguments"])
                break

    logging.debug("%s contains execute command [%s]", file, ' '.join(exe_cmd))
    return exe_cmd


def get_windows_launch_commands(game, files) -> list[LaunchCommand]:
    '''Find game executable file'''

    launch_commands = []

    # Get the execute command from the goggame info file
    goggame_file = os.path.join(game.install_dir, f'goggame-{game.id}.info')
    if os.path.exists(goggame_file):
        launch_commands.append(
            LaunchCommand(command=get_windows_exe_cmd_from_goggame_info(game, goggame_file), name="goginfo")
        )

    if not launch_commands and (launch_file_list := [file for file in files if re.match(r"^Launch .*\.lnk$", file)]):
        # Set Launch Game.lnk as executable
        launch_commands.append(LaunchCommand(
            command=[get_windows_runner(game), os.path.join(game.install_dir, launch_file_list[0])],
            name=launch_file_list[0]
        ))
        logging.debug("using link file [%s] as execute command", launch_file_list[0])

    if not launch_commands:
        # Find the executable files that are not blacklisted
        for file in files:
            if os.path.splitext(file.upper())[-1] not in [".EXE", ".LNK"]:
                continue
            if file in BINARY_NAMES_TO_IGNORE:
                continue
            launch_commands.append(
                LaunchCommand(
                    command=[
                        get_windows_runner(game), os.path.join(game.install_dir, file)
                    ],
                    name=file
                )
            )

    # Add the compatibility environment to every found command.
    environment = get_windows_environment(game)
    for launch_command in launch_commands:
        launch_command.command = ['env', *environment] + launch_command.command

    # Backwards compatibility with windows games installed before installer fixes.
    # Will not fix games requiring registry keys, since the paths will already
    # be borked through the old installer.
    wine_restore_game_link(game)

    return launch_commands


def get_dosbox_launch_commands(game, files) -> list[LaunchCommand]:
    dosbox_config = ""
    dosbox_config_single = ""
    for file in files:
        if re.match(r'^dosbox_?([a-z]|[A-Z]|\d)+\.conf$', file):
            dosbox_config = file
        if re.match(r'^dosbox_?([a-z]|[A-Z]|\d)+_single\.conf$', file):
            dosbox_config_single = file
    logging.info("Using system's dosbox to launch %s", game.name)
    return [
        LaunchCommand(
            command=["dosbox", "-conf", dosbox_config, "-conf", dosbox_config_single, "-no-console", "-c", "exit"],
            name="dosbox"
        )
    ]


def get_scummvm_launch_commands(game, files):
    scummvm_config = ""
    for file in files:
        if re.match(r'^.*\.ini$', file):
            scummvm_config = file
            break
    logging.info("Using system's scrummvm to launch %s", game.name)
    return [
        LaunchCommand(
            command=["scummvm", "-c", scummvm_config],
            name="scummvm"
        )
    ]


def get_start_script_launch_commands(game):
    return [
        LaunchCommand(
            command=[os.path.join(game.install_dir, "start.sh")],
            name="start.sh"
        )
    ]


def get_final_resort_launch_commands(game, files):
    # This is the final resort, applies to FTL
    launch_commands = []
    game_dir = "game"
    game_files = os.listdir(os.path.join(game.install_dir, game_dir)) if game_dir in files else []
    for file in game_files:
        if re.match(r'^goggame-[0-9]*\.info$', file):
            os.chdir(os.path.join(game.install_dir, game_dir))
            with open(file, 'r') as info_file:
                info = json.loads(info_file.read())
                launch_commands.append(LaunchCommand(
                    command=["./{}".format(info["playTasks"][0]["path"])],
                    name=info["playTasks"][0]["name"]
                ))
    return launch_commands


def set_fps_display(game):
    error_message = ""
    # Enable FPS Counter for Nvidia or AMD (Mesa) users
    if game.get_info(InfoKey.SHOW_FPS):
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "1"  # For Nvidia users + OpenGL/Vulkan games
        os.environ["GALLIUM_HUD"] = "simple,fps"  # For AMDGPU users + OpenGL games
        os.environ["VK_INSTANCE_LAYERS"] = "VK_LAYER_MESA_overlay"  # For AMDGPU users + Vulkan games
    else:
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "0"
        os.environ["GALLIUM_HUD"] = ""
        os.environ["VK_INSTANCE_LAYERS"] = ""
    return error_message


def run_game_subprocess(game, launch_command: LaunchCommand) -> tuple[str, subprocess.Popen]:
    try:
        process = subprocess.Popen(
            launch_command.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            cwd=game.install_dir
        )
        error_message = ""
    except FileNotFoundError:
        process = None
        error_message = _("No executable {} was found in {}").format(launch_command.name, game.install_dir)

    return error_message, process


def check_if_game_started_correctly(process, game):
    error_message = ""
    # Check if the application has started and see if it is still runnning after a short timeout
    try:
        process.wait(timeout=float(3))
        error_message = "Game start process has finished prematurely"
    except subprocess.TimeoutExpired:
        pass

    if error_message in ["Game start process has finished prematurely"]:
        error_message = check_if_game_start_process_spawned_final_process(error_message, game)

    # Set the error message to what's been received in stdout if not yet set
    if error_message:
        stdout, _ = process.communicate()
        error_message = stdout.decode("utf-8")
    return error_message


def check_if_game_start_process_spawned_final_process(error_message, game):
    ps_ef = subprocess.check_output(["ps", "-ef"]).decode("utf-8")
    ps_list = ps_ef.split("\n")
    for ps in ps_list:
        ps_split = ps.split()
        if len(ps_split) < 2:
            continue
        if not ps_split[1].isdigit():
            continue
        if int(ps_split[1]) > os.getpid() and game.get_install_directory_name() in ps:
            error_message = ""
            break
    return error_message


def send_game_output_to_stdout(process):

    def _internal_call(process):
        for line in iter(process.stdout.readline, b''):
            print(line.decode('utf-8'), end='')  # TODO Is this intentionally a print statement?
        process.stdout.close()
        process.wait()

    t = threading.Thread(target=_internal_call, args=(process,))
    t.start()
