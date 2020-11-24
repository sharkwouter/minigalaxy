import os
import subprocess
import shutil
import re
import json
import gi
import glob
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
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
        error_message = check_if_game_started_correctly(process)
    return error_message


    # Show the error as both a dialog and in the terminal
    error_text = _("Failed to start {}:").format(game.name)
    print(error_text)
    print(error_message)
    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.ERROR,
        parent=parent_window.parent,
        modal=True,
        buttons=Gtk.ButtonsType.CLOSE,
        text=error_text
    )
    dialog.format_secondary_text(error_message)
    dialog.run()
    dialog.destroy()


def __get_execute_command(game) -> list:
    files = os.listdir(game.install_dir)

    # Windows
    if "unins000.exe" in files:
        prefix = os.path.join(game.install_dir, "prefix")
        os.environ["WINEPREFIX"] = prefix

        # Find game executable file
        for file in files:
            if re.match(r'^goggame-[0-9]*\.info$', file):
                os.chdir(game.install_dir)
                with open(file, 'r') as info_file:
                    info = json.loads(info_file.read())
                    # if we have the workingDir property, start the executable at that directory
                    if "workingDir" in info["playTasks"][0]:
                        return ["wine", "start","/b","/wait","/d", info["playTasks"][0]["workingDir"], info["playTasks"][0]["path"]]
                    return ["wine", info["playTasks"][0]["path"]]

        # in case no goggame info file was found
        executables = glob.glob(game.install_dir + '/*.exe')
        executables.remove(os.path.join(game.install_dir, "unins000.exe"))
        filename = os.path.splitext(os.path.basename(executables[0]))[0] + '.exe'
        return ["wine", filename]

    # Dosbox
    if "dosbox" in files and shutil.which("dosbox"):
        for file in files:
            if re.match(r'^dosbox_?([a-z]|[A-Z]|[0-9])+\.conf$', file):
                dosbox_config = file
            if re.match(r'^dosbox_?([a-z]|[A-Z]|[0-9])+_single\.conf$', file):
                dosbox_config_single = file
        if dosbox_config and dosbox_config_single:
            print("Using system's dosbox to launch {}".format(game.name))
            return ["dosbox", "-conf", dosbox_config, "-conf", dosbox_config_single, "-no-console", "-c", "exit"]

    # ScummVM
    if "scummvm" in files and shutil.which("scummvm"):
        for file in files:
            if re.match(r'^.*\.ini$', file):
                scummvm_config = file
                break
        if scummvm_config:
            print("Using system's scrummvm to launch {}".format(game.name))
            return ["scummvm", "-c", scummvm_config]

    # Wine
    if "prefix" in files and shutil.which("wine"):
        # This still needs to be implemented
        return [os.path.join(game.install_dir, "start.sh")]

    # None of the above, but there is a start script
    if "start.sh" in files:
        return [os.path.join(game.install_dir, "start.sh")]

    # This is the final resort, applies to FTL
    if "game" in files:
        game_files = os.listdir("game")
        for file in game_files:
            if re.match(r'^goggame-[0-9]*\.info$', file):
                os.chdir(os.path.join(game.install_dir, "game"))
                with open(file, 'r') as info_file:
                    info = json.loads(info_file.read())
                    return ["./{}".format(info["playTasks"][0]["path"])]

    # If no executable was found at all, raise an error
    raise FileNotFoundError()


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
        process = subprocess.Popen(__get_execute_command(game), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        error_message = ""
    except FileNotFoundError:
        process = None
        error_message = _("No executable was found in {}").format(game.install_dir)

    # restore the working directory
    os.chdir(working_dir)
    return error_message, process


def check_if_game_started_correctly(process):
    error_message = ""
    # Check if the application has started and see if it is still runnning after a short timeout
    try:
        process.wait(timeout=float(3))
#        error_message = "" if process.poll() == 0 else "No error message was returned"
        error_message = "No error message was returned"
    except subprocess.TimeoutExpired:
        pass

    # Set the error message to what's been received in std error if not yet set
    if error_message:
        stdout, stderror = process.communicate()
        if stderror:
            error_message = stderror.decode("utf-8")
        elif stdout:
            error_message = stdout.decode("utf-8")
    return error_message

