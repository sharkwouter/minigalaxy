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


def config_game(game, options):

    prefix_dir = os.path.join(Config.get("install_dir"), "prefix")
    prefix = os.path.join(prefix_dir, game.name)

    os.environ["WINEPREFIX"] = prefix

    if options == "winecfg":
        subprocess.run(['wine', 'winecfg'])
    elif options == "regedit":
        subprocess.run(['wine', 'regedit'])


def start_game(game, parent_window=None) -> subprocess:
    error_message = ""
    process = None

    __set_fps_display()

    # Change the directory to the install dir
    working_dir = os.getcwd()
    os.chdir(game.install_dir)
    try:
        process = subprocess.Popen(__get_execute_command(game), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        error_message = _("No executable was found in {}").format(game.install_dir)

    # restore the working directory
    os.chdir(working_dir)

    # Check if the application has started and see if it is still runnning after a short timeout
    if process:
        try:
            process.wait(timeout=float(3))
        except subprocess.TimeoutExpired:
            return process
    elif not error_message:
        error_message = _("Couldn't start subprocess")

    # Set the error message to what's been received in std error if not yet set
    if not error_message:
        stdout, stderror = process.communicate()
        error_message = stderror.decode("utf-8")
        stdout_message = stdout.decode("utf-8")
        if not error_message:
            if stdout:
                error_message = stdout_message
            else:
                error_message = _("No error message was returned")

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
    if shutil.which("wine"):
        prefix_dir = os.path.join(Config.get("install_dir"), "prefix")
        prefix = os.path.join(prefix_dir, game.name)
        os.environ["WINEPREFIX"] = prefix

        # Find game executable file
        goggame_info = os.path.join(game.install_dir, "goggame-" + str(game.id) + ".info")

        if os.path.isfile(goggame_info):
            with open(goggame_info) as info_data:
                info_dict = json.load(info_data)
                path_name = info_dict.get("playTasks")
                filename = path_name[0]["path"]

            return ["wine", filename]
    else:
        filepath = glob.glob(game.install_dir + '/*.exe')[0]
        filename = os.path.splitext(os.path.basename(filepath))[0] + '.exe'
        return ["wine", filename]

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


def __set_fps_display():
    # Enable FPS Counter for Nvidia or AMD (Mesa) users
    if Config.get("show_fps"):
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "1"  # For Nvidia users
        os.environ["GALLIUM_HUD"] = "simple,fps"  # For AMDGPU users
    elif Config.get("show_fps") is False:
        os.environ["__GL_SHOW_GRAPHICS_OSD"] = "0"  # For Nvidia users
        os.environ["GALLIUM_HUD"] = ""
