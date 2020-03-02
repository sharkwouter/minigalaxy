import os
import shutil
import zipfile
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR
from minigalaxy.config import Config


def install_game(game, installer, parent_window=None) -> None:
    if not os.path.exists(installer):
        GLib.idle_add(__show_installation_error, game, _("{} failed to download".format(installer)), parent_window)
        raise FileNotFoundError("The installer {} does not exist".format(installer))

    # Make a temporary empty directory for extracting the installer
    temp_dir = os.path.join(CACHE_DIR, "extract/{}".format(game.id))
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)

    # Extract the installer
    try:
        with zipfile.ZipFile(installer) as archive:
            for member in archive.namelist():
                file = archive.getinfo(member)
                archive.extract(file, temp_dir)
                # Set permissions
                attr = file.external_attr >> 16
                os.chmod(os.path.join(temp_dir, member), attr)
    except zipfile.BadZipFile as e:
        GLib.idle_add(__show_installation_error, game, _("{} could not be unzipped".format(installer)), parent_window)
        raise e

    # Make sure the install directory exists
    library_dir = Config.get("install_dir")
    if not os.path.exists(library_dir):
        os.makedirs(library_dir)

    # Copy the game files into the correct directory
    shutil.move(os.path.join(temp_dir, "data/noarch"), game.install_dir)
    shutil.copyfile(
        os.path.join(THUMBNAIL_DIR, "{}.jpg".format(game.id)),
        os.path.join(game.install_dir, "thumbnail.jpg"),
    )

    # Remove the temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    if Config.get("keep_installers"):
        keep_dir = os.path.join(Config.get("install_dir"), "installer")
        if not os.path.exists(keep_dir):
            os.makedirs(keep_dir)
        try:
            os.rename(installer, os.path.join(keep_dir, "{}.sh".format(game.name)))
        except Exception:
            os.remove(installer)
    else:
        os.remove(installer)


def __show_installation_error(game, message, parent_window=None):
    error_message = [_("Failed to install {}".format(game.name)), message]
    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.ERROR,
        parent=parent_window.parent,
        modal=True,
        buttons=Gtk.ButtonsType.CLOSE,
        text=error_message[0]
    )
    dialog.format_secondary_text(error_message[1])
    dialog.run()
    dialog.destroy()
    print("{}: {}".format(error_message[0], error_message[1]))


def uninstall_game(game):
    shutil.rmtree(game.install_dir, ignore_errors=True)
