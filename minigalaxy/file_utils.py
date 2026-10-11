"""
Generic utilities related to files, directories and disk space etc.
"""

import shutil
import logging
import os

from minigalaxy.paths import CACHE_DIR


def get_available_disk_space(location):
    """Check disk space available to the user. This method uses the absolute path so
    symlinks to disks with sufficient space are correctly measured. Note this is
    a linux-specific command."""
    absolute_location = os.path.realpath(location)
    disk_status = os.statvfs(os.path.dirname(absolute_location))
    available_diskspace = disk_status.f_frsize * disk_status.f_bavail
    return available_diskspace


def make_tmp_dir(game):
    # Make a temporary empty directory for extracting the installer
    error_message = ""
    extract_dir = os.path.join(CACHE_DIR, "extract")
    temp_dir = os.path.join(extract_dir, str(game.id))
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, mode=0o755)
    return error_message, temp_dir


def safe_delete(file_list):
    """Tries to delete the given files without throwing exceptions where possible."""
    logging.info("Trying to safely delete: %s", file_list)
    for f in file_list:
        if is_empty_dir(f):
            os.rmdir(f)
        elif os.path.isfile(f):
            os.remove(f)


def is_empty_dir(path):
    return os.path.isdir(path) and not os.listdir(path)


def remove_empty_dirs_upwards(start_dir, stop_dirs):
    """Starting from a deeply nested empty directory, remove parents when their only child was one empty directory."""
    file_dir = start_dir
    while is_empty_dir(file_dir):
        logging.info("Remove now empty sub-directory [%s]", file_dir)
        os.rmdir(file_dir)
        file_dir = os.path.dirname(file_dir)
        if file_dir in stop_dirs:
            break
