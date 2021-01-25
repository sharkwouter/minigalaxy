import os
import subprocess
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR
from minigalaxy.config import Config
from minigalaxy import filesys_utils


def install_game(game, installer):
    error_message = ""
    tmp_dir = ""
    if not error_message:
        error_message = verify_installer_integrity(game, installer)
    if not error_message:
        error_message, tmp_dir = make_tmp_dir(game)
    if not error_message:
        error_message = extract_installer(game, installer, tmp_dir)
    if not error_message:
        error_message = move_and_overwrite(game, tmp_dir, game.install_dir)
    if not error_message:
        error_message = copy_thumbnail(game)
    if not error_message:
        error_message = remove_installer(installer)
    else:
        remove_installer(installer)
    if error_message:
        print(error_message)
    return error_message


def verify_installer_integrity(game, installer):
    error_message = ""
    if not os.path.exists(installer):
        error_message = _("{} failed to download.").format(installer)
    if not error_message:
        if game.platform == "linux":
            try:
                print("Executing integrity check for {}".format(installer))
                os.chmod(installer, 0o744)
                result = subprocess.run([installer, "--check"])
                if not result.returncode == 0:
                    error_message = _("{} was corrupted. Please download it again.").format(installer)
            except Exception as ex:
                # Any exception means the archive doesn't work, so we don't care with the error is
                print("Error, exception encountered: {}".format(ex))
                error_message = _("{} was corrupted. Please download it again.").format(installer)
        # TODO: Add verification for other platform
    return error_message


def make_tmp_dir(game):
    # Make a temporary empty directory for extracting the installer
    error_message = ""
    extract_dir = os.path.join(CACHE_DIR, "extract")
    temp_dir = os.path.join(extract_dir, str(game.id))
    if os.path.exists(temp_dir):
        filesys_utils.remove(temp_dir, recursive=True)
    filesys_utils.mkdir(temp_dir, parents=True)
    return error_message, temp_dir


def extract_installer(game, installer, temp_dir):
    # Extract the installer
    error_message = ""
    if game.platform == "linux":
        command = ["unzip", "-qq", installer, "-d", temp_dir]
    else:
        # Set the prefix for Windows games
        prefix_dir = os.path.join(game.install_dir, "prefix")
        if not os.path.exists(prefix_dir):
            filesys_utils.mkdir(prefix_dir, parents=True)

        # It's possible to set install dir as argument before installation
        command = ["env", "WINEPREFIX={}".format(prefix_dir), "wine", installer, "/dir={}".format(temp_dir)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    stdout, stderr = process.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    if (process.returncode not in [0, 1]) or \
       (process.returncode in [1] and "(attempting to process anyway)" not in stderr):
        error_message = _("The installation of {} failed. Please try again.").format(installer)
    elif len(os.listdir(temp_dir)) == 0:
        error_message = _("{} could not be unzipped.".format(installer))
    return error_message


def move_and_overwrite(game, temp_dir, target_dir):
    if game.platform == "linux":
        source_dir = os.path.join(temp_dir, "data/noarch")
    else:
        source_dir = temp_dir
    err_msg = filesys_utils.move(source_dir, target_dir)
    # Remove the temporary directory
    filesys_utils.remove(temp_dir, recursive=True)
    return err_msg


def copy_thumbnail(game):
    err_msg = ""
    new_thumbnail_path = os.path.join(game.install_dir, "thumbnail.jpg")
    # Copy thumbnail
    if not os.path.isfile(new_thumbnail_path):
        err_msg = filesys_utils.copy(os.path.join(THUMBNAIL_DIR, "{}.jpg".format(game.id)), new_thumbnail_path)
    return err_msg


def remove_installer(installer):
    err_msg = ""
    if not Config.get("keep_installers"):
        installer_directory = os.path.dirname(installer)
        if os.path.isdir(installer_directory):
            err_msg = filesys_utils.remove(installer_directory, recursive=True)
        else:
            err_msg = "No installer directory is present: {}".format(installer_directory)
    return err_msg


def uninstall_game(game):
    filesys_utils.remove(game.install_dir, recursive=True)
