import subprocess
import os
import shutil
from minigalaxy.config import Config
from minigalaxy.paths import CONFIG_DIR, CACHE_DIR


def _get_white_list():
    return [Config.get("install_dir"), CONFIG_DIR, CACHE_DIR]


def _get_black_list():
    important_user_dirs = ["", "DESKTOP", "DOCUMENTS", "DOWNLOAD", "MUSIC", "PICTURES", "PUBLICSHARE", "TEMPLATES",
                           "VIDEOS"]
    black_list = []
    for important_dir in important_user_dirs:
        black_list.append(subprocess.check_output(['xdg-user-dir', important_dir]).decode("utf-8").strip())
    return black_list


def _copy_move_and_overwrite(source, target, copy_or_move=""):
    err_msg = ""
    for src_dir, dirs, files in os.walk(source):
        destination_dir = src_dir.replace(source, target, 1)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        for src_file in files:
            file_to_copy = os.path.join(src_dir, src_file)
            dst_file = os.path.join(destination_dir, src_file)
            if copy_or_move == "copy":
                shutil.copy2(file_to_copy, dst_file)
            elif copy_or_move == "move":
                shutil.copy2(file_to_copy, dst_file)
            else:
                err_msg = "Unknown operation: {}".format(copy_or_move)
                break
    return err_msg


def check_if_accordance_with_lists(target):
    err_msd = ""
    if not target:
        err_msd = "Operation on no file was requested."
    inside_white_list = False
    for approve_dir in _get_white_list():
        if target.startswith(approve_dir):
            inside_white_list = True
            break
    is_blacklisted = False
    for deny_dir in _get_black_list():
        if target.strip() == deny_dir:
            is_blacklisted = True
            break
    if not inside_white_list:
        err_msd = "{} is not inside white list for file operations.".format(target)
    elif is_blacklisted:
        err_msd = "{} is on black list for file operations.".format(target)
    return err_msd


def remove(target="", recursive=False):
    err_msg = check_if_accordance_with_lists(target)
    if not err_msg:
        if not os.path.exists(target):
            err_msg = "No such a file or directory: {}".format(target)
        if os.path.isfile(target):
            os.remove(target)
        elif os.path.islink(target):
            os.unlink(target)
        elif os.path.isdir(target):
            if recursive:
                shutil.rmtree(target)
            else:
                err_msg = "Non recursive removal requested on directory:{}".format(target)
    return err_msg


def copy(source="", target="", recursive=False, overwrite=False):
    err_msg = ""
    if not source:
        err_msg = "No source file or directory was given."
    if not err_msg:
        err_msg = check_if_accordance_with_lists(target)
    if not err_msg:
        if not os.path.exists(source):
            err_msg = "No such a file or directory: {}".format(source)
        elif not os.path.isdir(os.path.dirname(target)):
            err_msg = "Directory for target copy doesnt exists: {}".format(os.path.dirname(target))
        elif os.path.isdir(source) and not recursive:
            err_msg = "Non recursive removal requested on directory:{}".format(target)
        elif os.path.exists(target) and not overwrite:
            err_msg = "Non overwrite operation, but target exists:{}".format(target)
        elif os.path.isfile(source) or os.path.islink(source):
            shutil.copy2(source, target)
        elif os.path.isdir(source):
            err_msg = _copy_move_and_overwrite(source, target, copy_or_move="copy")
    return err_msg

