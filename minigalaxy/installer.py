import os
import shutil
import subprocess
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR
from minigalaxy.config import Config


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
    error_message2 = remove_installer(installer)
    error_message = error_message2 if not error_message else error_message
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
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir, ignore_errors=True)
    os.makedirs(temp_dir, mode=0o755)
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
            os.makedirs(prefix_dir, mode=0o755)

        # It's possible to set install dir as argument before installation
        command = ["WINEPREFIX={}".format(prefix_dir), "wine", installer, "/dir={}".format(temp_dir)]
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
    # Copy the game files into the correct directory
    error_message = ""
    if game.platform == "linux":
        source_dir = os.path.join(temp_dir, "data/noarch")
    else:
        source_dir = temp_dir
    for src_dir, dirs, files in os.walk(source_dir):
        destination_dir = src_dir.replace(source_dir, target_dir, 1)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        for src_file in files:
            file_to_copy = os.path.join(src_dir, src_file)
            dst_file = os.path.join(destination_dir, src_file)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.move(file_to_copy, destination_dir)

    # Remove the temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    return error_message


def copy_thumbnail(game):
    error_message = ""
    # Copy thumbnail
    try:
        shutil.copyfile(
                        os.path.join(THUMBNAIL_DIR, "{}.jpg".format(game.id)),
                        os.path.join(game.install_dir, "thumbnail.jpg"),
                        )
    except Exception as e:
        error_message = e
    return error_message


def remove_installer(installer):
    error_message = ""
    if Config.get("keep_installers"):
        keep_dir = os.path.join(Config.get("install_dir"), "installer")
        download_dir = os.path.join(CACHE_DIR, "download")
        if not os.path.exists(keep_dir):
            os.makedirs(keep_dir, mode=0o755)
        try:
            # It's needed for multiple files
            for file in os.listdir(download_dir):
                shutil.move(download_dir + '/' + file, keep_dir + '/' + file)
        except Exception as ex:
            print("Encountered error while copying {} to {}. Got error: {}".format(installer, keep_dir, ex))
    elif os.path.exists(installer):
        os.remove(installer)
    return error_message


def uninstall_game(game):
    shutil.rmtree(game.install_dir, ignore_errors=True)
