import os
import subprocess
import shutil
import re
import json
import glob
from minigalaxy.translation import _
from minigalaxy.config import Config


def config_game(game):
    prefix = os.path.join(game.install_dir, "prefix")

    os.environ["WINEPREFIX"] = prefix
    subprocess.Popen(['wine', 'winecfg'])


def start_game(game):
    error_message = ""
    process = None
    if not error_message:
        error_message = set_fps_display()
    if not error_message:
        error_message, process = run_game_subprocess(game)
    if not error_message:
        error_message = check_if_game_started_correctly(process, game)
    if error_message:
        print(_("Failed to start {}:").format(game.name))
        print(error_message)
    return error_message


def get_execute_command(game) -> list:
    files = os.listdir(game.install_dir)
    launcher_type = determine_launcher_type(files)
    if launcher_type in ["windows"]:
        exe_cmd = get_windows_exe_cmd(game, files)
    elif launcher_type in ["dosbox"]:
        exe_cmd = get_dosbox_exe_cmd(game, files)
    elif launcher_type in ["scummvm"]:
        exe_cmd = get_scummvm_exe_cmd(game, files)
    elif launcher_type in ["start_script", "wine"]:
        exe_cmd = get_start_script_exe_cmd(game, files)
    elif launcher_type in ["final_resort"]:
        exe_cmd = get_final_resort_exe_cmd(game, files)
    else:
        # If no executable was found at all, raise an error
        raise FileNotFoundError()
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


def get_windows_exe_cmd(game, files):
    exe_cmd = [""]
    prefix = os.path.join(game.install_dir, "prefix")
    os.environ["WINEPREFIX"] = prefix
    command = game.get_info("command").split(" ")
    var = game.get_info("variable").split(" ")
    i = 0

    # Find game executable file
    for file in files:
        if re.match(r'^goggame-[0-9]*\.info$', file):
            os.chdir(game.install_dir)
            with open(file, 'r') as info_file:
                info = json.loads(info_file.read())
                # if we have the workingDir property, start the executable at that directory
                if "workingDir" in info["playTasks"][0] and info["playTasks"][0]["workingDir"]:
                    exe_cmd = ["wine", "start","/b","/wait","/d", info["playTasks"][0]["workingDir"], info["playTasks"][0]["path"]]
                else:
                    exe_cmd = ["wine", info["playTasks"][0]["path"]]
    if exe_cmd == [""]:
        # in case no goggame info file was found
        executables = glob.glob(game.install_dir + '/*.exe')
        executables.remove(os.path.join(game.install_dir, "unins000.exe"))
        filename = os.path.splitext(os.path.basename(executables[0]))[0] + '.exe'
        exe_cmd = ["wine", filename]

    # Check if variable environment are set.
    # Command can be empty
    if var[0] != "":
        while i < len(var):
            if i < len(var):
                exe_cmd.insert(i, var[i])
                i = i + 1
            else:
                break

    exe_cmd.extend(command)
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


def get_start_script_exe_cmd(game, files):
    command = game.get_info("command").split(" ")
    var = game.get_info("variable").split(" ")
    i = 0

    exec_start = [os.path.join(game.install_dir, "start.sh")]

    # Check if variable environment are set.
    # Command can be empty
    if var[0] != "":
        while i < len(var):
            if i < len(var):
                exec_start.insert(i, var[i])
                i = i + 1
            else:
                break

    exec_start.extend(command)
    return exec_start

def get_final_resort_exe_cmd(game, files):
    # This is the final resort, applies to FTL
    exe_cmd = [""]
    game_files = os.listdir("game")
    for file in game_files:
        if re.match(r'^goggame-[0-9]*\.info$', file):
            os.chdir(os.path.join(game.install_dir, "game"))
            with open(file, 'r') as info_file:
                info = json.loads(info_file.read())
                exe_cmd = ["./{}".format(info["playTasks"][0]["path"])]
    return exe_cmd


def set_fps_display():
    error_message = ""
    # Enable FPS Counter for Nvidia or AMD (Mesa) users
    if Config.get("show_fps"):
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "1"  # For Nvidia users + OpenGL/Vulkan games
        os.environ["GALLIUM_HUD"] = "simple,fps"  # For AMDGPU users + OpenGL games
        os.environ["VK_INSTANCE_LAYERS"] = "VK_LAYER_MESA_overlay"  # For AMDGPU users + Vulkan games
    else:
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "0"
        os.environ["GALLIUM_HUD"] = ""
        os.environ["VK_INSTANCE_LAYERS"] = ""
    return error_message


def run_game_subprocess(game):
    # Change the directory to the install dir
    working_dir = os.getcwd()
    os.chdir(game.install_dir)
    try:
        process = subprocess.Popen(get_execute_command(game), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        error_message = ""
    except FileNotFoundError:
        process = None
        error_message = _("No executable was found in {}").format(game.install_dir)

    # restore the working directory
    os.chdir(working_dir)
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

    # Set the error message to what's been received in std error if not yet set
    if error_message:
        stdout, stderror = process.communicate()
        if stderror:
            error_message = stderror.decode("utf-8")
        elif stdout:
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
        if int(ps_split[1]) > os.getpid() and game.name in ps:
            error_message = ""
            break
    return error_message
