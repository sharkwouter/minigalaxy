import os
import shutil
import zipfile
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR
from minigalaxy.config import Config


def install_game(game, installer) -> None:
    # Make a temporary empty directory for extracting the installer
    temp_dir = os.path.join(CACHE_DIR, "extract/{}".format(game.id))
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)

    # Extract the installer
    if os.path.exists(installer):
        installer_path = installer

    with zipfile.ZipFile(installer_path) as archive:
        for member in archive.namelist():
            file = archive.getinfo(member)
            archive.extract(file, temp_dir)
            # Set permissions
            attr = file.external_attr >> 16
            os.chmod(os.path.join(temp_dir, member), attr)

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
            os.rename(installer, keep_dir)
        except Exception:
            os.remove(installer)
    else:
        os.remove(installer)


def uninstall_game(game):
    shutil.rmtree(game.install_dir, ignore_errors=True)
