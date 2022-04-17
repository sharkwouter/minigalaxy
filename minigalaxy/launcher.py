import os
import subprocess
import shutil
import re
import json
import glob
import threading
from minigalaxy.translation import _


def get_wine_path(game):
    binary_name = "wine"
    custom_wine_path = game.get_info("custom_wine")
    if custom_wine_path and custom_wine_path != shutil.which(binary_name):
        binary_name = custom_wine_path
    return binary_name


def config_game(game):
    prefix = os.path.join(game.install_dir, "prefix")

    os.environ["WINEPREFIX"] = prefix
    subprocess.Popen([get_wine_path(game), 'winecfg'])


def regedit_game(game):
    prefix = os.path.join(game.install_dir, "prefix")

    os.environ["WINEPREFIX"] = prefix
    subprocess.Popen([get_wine_path(game), 'regedit'])


def winetricks_game(game):
    prefix = os.path.join(game.install_dir, "prefix")

    os.environ["WINEPREFIX"] = prefix
    subprocess.Popen(['winetricks'])


def start_game(game):
    error_message = ""
    process = None
    if not error_message:
        error_message = set_fps_display(game)
    if not error_message:
        error_message, process = run_game_subprocess(game)
    if not error_message:
        error_message = check_if_game_started_correctly(process, game)
    if not error_message:
        send_game_output_to_stdout(process)
    if error_message:
        print(_("Failed to start {}:").format(game.name))
        print(error_message)
    return error_message


def get_execute_command(game) -> list:
    files = os.listdir(game.install_dir)
    launcher_type = determine_launcher_type(files)
    if launcher_type in ["start_script", "wine"]:
        exe_cmd = get_start_script_exe_cmd()
    elif launcher_type == "windows":
        exe_cmd = get_windows_exe_cmd(game, files)
    elif launcher_type == "dosbox":
        exe_cmd = get_dosbox_exe_cmd(game, files)
    elif launcher_type == "scummvm":
        exe_cmd = get_scummvm_exe_cmd(game, files)
    elif launcher_type == "final_resort":
        exe_cmd = get_final_resort_exe_cmd(game, files)
    else:
        # If no executable was found at all, raise an error
        raise FileNotFoundError()
    if game.get_info("use_gamemode") is True:
        exe_cmd.insert(0, "gamemoderun")
    if game.get_info("use_mangohud") is True:
        exe_cmd.insert(0, "mangohud")
        exe_cmd.insert(1, "--dlsym")
    exe_cmd = get_exe_cmd_with_var_command(game, exe_cmd)
    return exe_cmd


def determine_launcher_type(files):
    launcher_type = "unknown"
    if "unins000.exe" in files:
        launcher_type = "windows"
    elif "dosbox" in files and shutil.which("dosbox"):
        launcher_type = "dosbox"
    elif "scummvm" in files and shutil.which("scummvm"):
        launcher_type = "scummvm"
    elif "prefix" in files and shutil.which("wine"):
        launcher_type = "wine"
    elif "start.sh" in files:
        launcher_type = "start_script"
    elif "game" in files:
        launcher_type = "final_resort"
    return launcher_type


def get_exe_cmd_with_var_command(game, exe_cmd):
    var_list = game.get_info("variable").split()
    command_list = game.get_info("command").split()

    if var_list:
        if var_list[0] not in ["env"]:
            var_list.insert(0, "env")

    exe_cmd = var_list + exe_cmd + command_list
    return exe_cmd


def get_windows_exe_cmd(game, files):
    exe_cmd = [""]
    prefix = os.path.join(game.install_dir, "prefix")
    os.environ["WINEPREFIX"] = prefix

    # Find game executable file
    for file in files:
        if re.match(r'^goggame-[0-9]*\.info$', file):
            os.chdir(game.install_dir)
            with open(file, 'r') as info_file:
                info = json.loads(info_file.read())
                # if we have the workingDir property, start the executable at that directory
                if info["playTasks"]:
                    if "workingDir" in info["playTasks"][0] and info["playTasks"][0]["workingDir"]:
                        exe_cmd = [get_wine_path(game), "start", "/b", "/wait", "/d", info["playTasks"][0]["workingDir"],
                                   info["playTasks"][0]["path"]]
                    else:
                        exe_cmd = [get_wine_path(game), info["playTasks"][0]["path"]]
    if exe_cmd == [""]:
        # in case no goggame info file was found
        executables = glob.glob(game.install_dir + '/*.exe')
        executables.remove(os.path.join(game.install_dir, "unins000.exe"))
        filename = os.path.splitext(os.path.basename(executables[0]))[0] + '.exe'
        exe_cmd = [get_wine_path(game), filename]

    return exe_cmd


def get_dosbox_exe_cmd(game, files):
    dosbox_config = ""
    dosbox_config_single = ""
    for file in files:
        if re.match(r'^dosbox_?([a-z]|[A-Z]|[0-9])+\.conf$', file):
            dosbox_config = file
        if re.match(r'^dosbox_?([a-z]|[A-Z]|[0-9])+_single\.conf$', file):
            dosbox_config_single = file
    print("Using system's dosbox to launch {}".format(game.name))
    return ["dosbox", "-conf", dosbox_config, "-conf", dosbox_config_single, "-no-console", "-c", "exit"]


def get_scummvm_exe_cmd(game, files):
    scummvm_config = ""
    for file in files:
        if re.match(r'^.*\.ini$', file):
            scummvm_config = file
            break
    print("Using system's scrummvm to launch {}".format(game.name))
    return ["scummvm", "-c", scummvm_config]


def get_start_script_exe_cmd():
    return ["./start.sh"]


def get_final_resort_exe_cmd(game, files):
    # This is the final resort, applies to FTL
    exe_cmd = [""]
    game_dir = "game"
    game_files = os.listdir(os.path.join(game.install_dir, game_dir)) if game_dir in files else []
    for file in game_files:
        if re.match(r'^goggame-[0-9]*\.info$', file):
            os.chdir(os.path.join(game.install_dir, game_dir))
            with open(file, 'r') as info_file:
                info = json.loads(info_file.read())
                exe_cmd = ["./{}".format(info["playTasks"][0]["path"])]
    return exe_cmd


def set_fps_display(game):
    error_message = ""
    # Enable FPS Counter for Nvidia or AMD (Mesa) users
    if game.get_info("show_fps"):
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "1"  # For Nvidia users + OpenGL/Vulkan games
        os.environ["GALLIUM_HUD"] = "simple,fps"  # For AMDGPU users + OpenGL games
        os.environ["VK_INSTANCE_LAYERS"] = "VK_LAYER_MESA_overlay"  # For AMDGPU users + Vulkan games
    else:
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "0"
        os.environ["GALLIUM_HUD"] = ""
        os.environ["VK_INSTANCE_LAYERS"] = ""
    return error_message


def run_game_subprocess(game):
    try:
        process = subprocess.Popen(
            get_execute_command(game),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            cwd=game.install_dir
        )
        error_message = ""
    except FileNotFoundError:
        process = None
        error_message = _("No executable was found in {}").format(game.install_dir)

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
            print(line.decode('utf-8'), end='')
        process.stdout.close()
        process.wait()
    t = threading.Thread(target=_internal_call, args=(process,))
    t.start()
