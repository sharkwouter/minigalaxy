import subprocess
import os
import shutil
from minigalaxy.config import Config
from minigalaxy.paths import CONFIG_DIR, CACHE_DIR


def get_white_list():
    return [Config.get("install_dir"), CONFIG_DIR, CACHE_DIR]


def get_black_list():
    important_user_dirs = ["", "DESKTOP", "DOCUMENTS", "DOWNLOAD", "MUSIC", "PICTURES", "PUBLICSHARE", "TEMPLATES_DIR",
                           "VIDEOS"]
    black_list = []
    for important_dir in important_user_dirs:
        black_list.append(subprocess.check_output(['xdg-user-dir', important_dir]).decode("utf-8").strip())
    return black_list


def check_if_accordance_with_lists(target):
    err_msd = ""
    if not target:
        err_msd = "Operaation on no file was requested."
    inside_white_list = False
    for approve_dir in get_white_list():
        if target.startswith(approve_dir):
            inside_white_list = True
            break
    is_blacklisted = False
    for deny_dir in get_black_list():
        if target.strip() == deny_dir:
            is_blacklisted = True
            break
    if not inside_white_list:
        err_msd = "{} is not inside white list for file operations".format(target)
    elif is_blacklisted:
        err_msd = "{} is on black list for file operations".format(target)
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
