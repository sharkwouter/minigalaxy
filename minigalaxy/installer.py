import os
import shutil
import subprocess
import hashlib
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
        for installer_file_name in os.listdir(os.path.dirname(installer)):
            hash_md5 = hashlib.md5()
            with open(os.path.join(os.path.dirname(installer), installer_file_name), "rb") as installer_file:
                for chunk in iter(lambda: installer_file.read(4096), b""):
                    hash_md5.update(chunk)
            calculated_checksum = hash_md5.hexdigest()
            if installer_file_name in game.md5sum:
                if game.md5sum[installer_file_name] == calculated_checksum:
                    print("{} integrity is preserved. MD5 is: {}".format(installer_file_name, calculated_checksum))
                else:
                    error_message = _("{} was corrupted. Please download it again.").format(installer_file_name)
                    break
            else:
                print("Warning. No info about correct {} MD5 checksum".format(installer_file_name))
    return error_message


def make_tmp_dir(game):
    # Make a temporary empty directory for extracting the installer
    error_message = ""
    extract_dir = os.path.join(CACHE_DIR, "extract")
    temp_dir = os.path.join(extract_dir, str(game.id))
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
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
        command = ["env", "WINEPREFIX={}".format(prefix_dir), "wine", installer, "/dir={}".format(temp_dir), "/VERYSILENT"]
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
    new_thumbnail_path = os.path.join(game.install_dir, "thumbnail.jpg")
    # Copy thumbnail
    if not os.path.isfile(new_thumbnail_path):
        try:
            shutil.copyfile(
                            os.path.join(THUMBNAIL_DIR, "{}.jpg".format(game.id)),
                            new_thumbnail_path,
                            )
        except Exception as e:
            error_message = e
    return error_message


def remove_installer(installer):
    error_message = ""
    if not Config.get("keep_installers"):
        installer_directory = os.path.dirname(installer)
        if os.path.isdir(installer_directory):
            shutil.rmtree(installer_directory, ignore_errors=True)
        else:
            error_message = "No installer directory is present: {}".format(installer_directory)
    return error_message


def uninstall_game(game):
    shutil.rmtree(game.install_dir, ignore_errors=True)
