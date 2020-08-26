import os
import shutil
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR
from minigalaxy.config import Config


def install_game(game, installer, main_window=None) -> None:
    if not os.path.exists(installer):
        GLib.idle_add(__show_installation_error, game, _("{} failed to download.").format(installer), main_window)
        raise FileNotFoundError("The installer {} does not exist".format(installer))

    if game.platform == "linux":
        if not __verify_installer_integrity(installer):
            GLib.idle_add(__show_installation_error, game, _("{} was corrupted. Please download it again.").format(installer), main_window)
            os.remove(installer)
            raise FileNotFoundError("The installer {} was corrupted".format(installer))

        # Make a temporary empty directory for extracting the installer
        temp_dir = os.path.join(CACHE_DIR, "extract/{}".format(game.id))
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir)

        # Extract the installer
        subprocess.call(["unzip", "-qq", installer, "-d", temp_dir])
        if len(os.listdir(temp_dir)) == 0:
            GLib.idle_add(__show_installation_error, game, _("{} could not be unzipped.").format(installer), main_window)
            raise CannotOpenZipContent(_("{} could not be unzipped.").format(installer))

        # Make sure the install directory exists
        library_dir = Config.get("install_dir")
        if not os.path.exists(library_dir):
            os.makedirs(library_dir)

        # Copy the game files into the correct directory
        shutil.move(os.path.join(temp_dir, "data/noarch"), game.install_dir)

        # Remove the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        # Set the prefix for Windows games
        prefix_dir = os.path.join(game.install_dir, "prefix")
        if not os.path.exists(prefix_dir):
            os.makedirs(prefix_dir)

        os.environ["WINEPREFIX"] = prefix_dir

        # It's possible to set install dir as argument before installation
        command = ["wine", installer, "/dir=" + game.install_dir]
        process = subprocess.Popen(command)
        process.wait()
        if process.returncode != 0:
            GLib.idle_add(__show_installation_error, game,
                      _("The installation of {} failed. Please try again.").format(installer), main_window)
            return

    shutil.copyfile(
        os.path.join(THUMBNAIL_DIR, "{}.jpg".format(game.id)),
        os.path.join(game.install_dir, "thumbnail.jpg"),
    )

    if Config.get("keep_installers"):
        keep_dir = os.path.join(Config.get("install_dir"), "installer")
        download_dir = os.path.join(CACHE_DIR, "download")
        if not os.path.exists(keep_dir):
            os.makedirs(keep_dir)
        try:
            # It's needed for multiple files
            for file in os.listdir(download_dir):
                shutil.move(download_dir + '/' + file, keep_dir + '/' + file)
        except Exception as ex:
            print("Encountered error while copying {} to {}. Got error: {}".format(installer, keep_dir, ex))
    else:
        os.remove(installer)


def __show_installation_error(game, message, main_window=None):
    error_message = [_("Failed to install {}").format(game.name), message]
    print("{}: {}".format(error_message[0], error_message[1]))
    main_window.show_error(error_message[0], error_message[1])


class CannotOpenZipContent(Exception):
    pass


def __verify_installer_integrity(installer):
    try:
        print("Executing integrity check for {}".format(installer))
        os.chmod(installer, 0o744)
        result = subprocess.run([installer, "--check"])
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as ex:
        # Any exception means the archive doesn't work, so we don't care with the error is
        print("Error, exception encountered: {}".format(ex))
        return False


def uninstall_game(game):
    shutil.rmtree(game.install_dir, ignore_errors=True)
