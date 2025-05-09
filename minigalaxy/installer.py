import sys
import os
import shutil
import shlex
import subprocess
import hashlib
import textwrap
import time
import re

from minigalaxy.config import Config
from minigalaxy.constants import GAME_LANGUAGE_IDS
from minigalaxy.game import Game
from minigalaxy.logger import logger
from minigalaxy.translation import _
from minigalaxy.launcher import get_execute_command, get_wine_path, wine_restore_game_link
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, APPLICATIONS_DIR, WINE_RES_PATH, DOWNLOAD_DIR


def get_available_disk_space(location):
    """Check disk space available to the user. This method uses the absolute path so
    symlinks to disks with sufficient space are correctly measured. Note this is
    a linux-specific command."""
    absolute_location = os.path.realpath(location)
    disk_status = os.statvfs(os.path.dirname(absolute_location))
    available_diskspace = disk_status.f_frsize * disk_status.f_bavail
    return available_diskspace


def get_game_size_from_unzip(installer):
    var = subprocess.Popen(['unzip', '-v', installer], stdout=subprocess.PIPE)
    output = var.communicate()[0].decode("utf-8")
    lines_list = output.split("\n")
    if len(lines_list) > 2 and not lines_list[-1].strip():
        last_line = lines_list[-2].strip()
    else:
        last_line = lines_list[-1].strip()
    size_value = int(last_line.split()[0])
    return size_value


def check_diskspace(required_size, location):
    """This method will return True when the disk space available is sufficient
    for the Download and Install. If not sufficient, it returns False."""
    installed_game_size = int(required_size)
    diskspace_available = get_available_disk_space(location)
    return diskspace_available >= installed_game_size


def install_game(  # noqa: C901
        game: Game,
        installer: str,
        language: str,
        install_dir: str,
        keep_installers: bool,
        create_desktop_file: bool,
        file_list=None
):
    error_message = ""
    tmp_dir = ""
    logger.info("Installing {}".format(game.name))
    try:
        if not error_message:
            error_message = verify_installer_integrity(game, installer)
        if not error_message:
            error_message = verify_disk_space(game, installer)
        if not error_message:
            error_message, tmp_dir = make_tmp_dir(game)
        if not error_message:
            error_message, installed_to_tmp = extract_installer(game, installer, tmp_dir, language)
        if not error_message:
            error_message = move_and_overwrite(game, tmp_dir, installed_to_tmp)
        if not error_message:
            error_message = copy_thumbnail(game)
        if not error_message and create_desktop_file:
            error_message = create_applications_file(game)
    except Exception:
        logger.error("Error installing game %s", game.name, exc_info=1)
        error_message = _("Unhandled error.")
    _removal_error = remove_installer(game, installer, install_dir, keep_installers, file_list)
    error_message = error_message or _removal_error or postinstaller(game)
    if error_message:
        logger.error(error_message)
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
                    logger.info("%s integrity is preserved. MD5 is: %s", installer_file_name, calculated_checksum)
                else:
                    error_message = _("{} was corrupted. Please download it again.").format(installer_file_name)
                    break
            else:
                logger.warning("Warning. No info about correct %s MD5 checksum", installer_file_name)
    return error_message


def verify_disk_space(game, installer):
    err_msg = ""
    if game.platform == "linux":
        required_space = get_game_size_from_unzip(installer)
        if not check_diskspace(required_space, game.install_dir):
            err_msg = _("Not enough space to extract game. Required: {} Available: {}"
                        ).format(required_space, get_available_disk_space(game.install_dir))
    return err_msg


def make_tmp_dir(game):
    # Make a temporary empty directory for extracting the installer
    error_message = ""
    extract_dir = os.path.join(CACHE_DIR, "extract")
    temp_dir = os.path.join(extract_dir, str(game.id))
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, mode=0o755)
    return error_message, temp_dir


def extract_installer(game: Game, installer: str, temp_dir: str, language: str):
    # Extract the installer
    if game.platform in ["linux"]:
        return extract_linux(installer, temp_dir)
    else:
        return extract_windows(game, installer, language)


def extract_linux(installer, temp_dir):
    err_msg = ""
    command = ["unzip", "-qq", installer, "-d", temp_dir]
    stdout, stderr, exitcode = _exe_cmd(command)
    if (exitcode not in [0]) and \
       (exitcode not in [1] and "(attempting to process anyway)" not in stderr):
        err_msg = _("The installation of {} failed. Please try again.").format(installer)
    elif len(os.listdir(temp_dir)) == 0:
        err_msg = _("{} could not be unzipped.".format(installer))
    return err_msg, True


def extract_windows(game: Game, installer: str, language: str):
    languageLog = os.path.join(game.install_dir, 'minigalaxy_setup_languages.log')
    if not os.path.exists(game.install_dir):
        os.makedirs(game.install_dir)
    game_lang = match_game_lang_to_installer(installer, language, languageLog)
    logger.info(f'use {game_lang} for installer')

    return extract_by_wine(game, installer, game_lang), False


def extract_by_wine(game, installer, game_lang, config=Config()):
    # Set the prefix for Windows games
    prefix_dir = os.path.join(game.install_dir, "prefix")
    wine_env = [
        f"WINEPREFIX={prefix_dir}",
        "WINEDLLOVERRIDES=winemenubuilder.exe=d"
    ]
    wine_bin = get_wine_path(game)

    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir, mode=0o755)
        '''
        Creating the prefix before modifying dosdevices
        Use regedit import as first command and try to disable the menubuilder for good
        So that it will also be disabled when patches, updates or dependencies like directx are installed
        later on by the game itself from within the prefix. Happened with UE4.
        '''
        command = ["env", *wine_env, wine_bin, "regedit", f"{WINE_RES_PATH}/disable_menubuilder.reg"]
        if not try_wine_command(command):
            return _("Wineprefix creation failed.")

    # calculate relative link prefix/c/game to game.install_dir
    # keeping it relative makes sure that the game can be moved around without stuff breaking
    wine_restore_game_link(game)
    # It's possible to set install dir as argument before installation
    installer_cmd_basic = [
        'env', *wine_env, wine_bin, installer,
        # use hard-coded directory name within wine, its just a backlink to game.install_dir
        # this avoids issues with varying path and spaces
        "/DIR=c:\\game",
        # capture information for debugging during install
        f"/LANG={game_lang}",
        "/LOG=c:\\install.log",
    ]
    installer_args_full = [
        "/SAVEINF=c:\\setup.inf",
        # installers can run very long, give at least a bit of visual feedback
        # by using /SILENT instead of /VERYSILENT
        '/SP-', '/SILENT', '/NORESTART', '/SUPPRESSMSGBOXES'
    ]

    # first, try full unattended install.
    success = try_wine_command(installer_cmd_basic + installer_args_full)
    if not success:
        # some games will reject the /SILENT flag
        # because they require the user to accept EULA at the beginning
        # Open normal installer as fallback and hope for the best
        print('Unattended install failed. Try install with wizard dialog.', file=sys.stderr)
        success = try_wine_command(installer_cmd_basic)

    if not success:
        return _("Wine extraction failed.")

    return ""


def try_wine_command(command_arr):
    print('trying to run wine command:', shlex.join(command_arr))
    stdout, stderr, exitcode = _exe_cmd(command_arr, True)
    if exitcode not in [0]:
        print(stderr, file=sys.stderr)
        return False

    return True


def move_and_overwrite(game, temp_dir, installed_to_tmp):
    # Copy the game files into the correct directory
    error_message = ""
    source_dir = (os.path.join(temp_dir, "data", "noarch") if game.platform == 'linux' else
                  temp_dir)
    target_dir = game.install_dir

    if installed_to_tmp:
        _mv(source_dir, target_dir)
    else:
        logger.info(f'installation of {game.name} did not use temporary directory - nothing to move')

    # Remove the temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    if game.platform in ["windows"] and "unins000.exe" not in os.listdir(game.install_dir):
        open(os.path.join(game.install_dir, "unins000.exe"), "w").close()
    return error_message


def copy_thumbnail(game):
    error_message = ""
    new_thumbnail_path = os.path.join(game.install_dir, "thumbnail.jpg")
    # Copy thumbnail
    if not os.path.isfile(new_thumbnail_path):
        try:
            shutil.copyfile(os.path.join(THUMBNAIL_DIR, "{}.jpg".format(game.id)),
                            new_thumbnail_path)
        except Exception as e:
            error_message = e
    return error_message


def get_exec_line(game):
    """Handles quoting of Exec key which is stricter than regular shell quoting
    See https://specifications.freedesktop.org/desktop-entry-spec/latest/exec-variables.html for details"""
    chars_to_quote = re.compile(r'(["$`\\])', re.ASCII)  # double-qoute, dollar and backtick
    replace_pattern = r'\\\1'
    exe_cmd_list = get_execute_command(game)
    for i in range(len(exe_cmd_list)):
        entry = exe_cmd_list[i]
        if chars_to_quote.search(entry) is not None:
            entry = f'"{chars_to_quote.sub(replace_pattern, entry)}"'
            """backslashes in quotes nightmare: double backslash is one literal
            but it must be escaped again because it is processed twice:
            once as string before unquoting, then the unquoting itself
            From Exec doc:
            > [...] to unambiguously represent a literal backslash character in a quoted argument [...]
            > requires [...] four successive backslash characters ("\\\\")."""
            entry = entry.replace('\\\\', '\\\\\\\\')
        elif ' ' in entry:  # only need to treat blanks by quoting if not quoted because of special characters anyway
            entry = f'"{entry}"'

        exe_cmd_list[i] = entry
    return " ".join(exe_cmd_list)


def create_applications_file(game, override=False):
    error_message = ""
    path_to_shortcut = os.path.join(APPLICATIONS_DIR, "{}.desktop".format(game.get_stripped_name(to_path=True)))
    # Create desktop file definition
    local_icon_dir = os.path.join(game.install_dir, 'support')
    local_icon_file = os.path.join(local_icon_dir, 'icon.png')
    desktop_context = {
        "game_bin_path": get_exec_line(game),
        "game_name": game.name,
        "game_install_dir": game.install_dir,
        "game_icon_path": local_icon_file
        }
    desktop_definition = """\
        [Desktop Entry]
        Type=Application
        Terminal=false
        StartupNotify=true
        Exec={game_bin_path}
        Path={game_install_dir}
        Name={game_name}
        Icon={game_icon_path}
        Categories=Game""".format(**desktop_context)

    file_exists = os.path.isfile(path_to_shortcut)
    try:
        if file_exists and override:
            os.remove(path_to_shortcut)
        elif file_exists:
            return error_message

        if os.path.exists(game.get_cached_icon_path()):
            os.makedirs(local_icon_dir, mode=0o755, exist_ok=True)
            shutil.copy(game.get_cached_icon_path(), local_icon_file)

        with open(path_to_shortcut, 'w+') as desktop_file:
            desktop_file.writelines(textwrap.dedent(desktop_definition))
    except Exception as e:
        os.remove(path_to_shortcut)
        error_message = e
    return error_message


def compare_directories(dir1, dir2):
    files_1 = []
    files_2 = []

    if os.path.isdir(dir1):
        files_1 = os.listdir(dir1)
    if os.path.isdir(dir2):
        files_2 = os.listdir(dir2)

    if not set(files_1).issubset(set(files_2)):
        return False

    result = True
    for f in files_1:
        if os.path.getsize(os.path.join(dir1, f)) != \
           os.path.getsize(os.path.join(dir2, f)):
            result = False

    return result


def remove_installer(game: Game, installer: str, keep_installers_dir: str, keep_installers: bool, file_list=None):
    installer_dir = os.path.dirname(installer)
    if not os.path.isdir(installer_dir):
        error_message = "No installer directory is present: {}".format(installer_dir)
        return error_message

    installer_root_dirs = [
        os.path.realpath(DOWNLOAD_DIR),
        keep_installers_dir
    ]

    keep_files = []
    if keep_installers and file_list:
        keep_files = file_list
    elif keep_installers:
        # assume all support files are named with the same prefix and only differ in ending
        # we run into this case when installing from local file by ui clicking instead of from the download_finish callback
        installer_prefix = os.path.splitext(os.path.basename(installer))[0]
        for f in os.listdir(installer_dir):
            fullpath = os.path.join(installer_dir, f)
            if os.path.isfile(fullpath) and f.startswith(installer_prefix):
                keep_files.append(fullpath)

    logger.info("Cleaning [%s] - keep_files:%s", installer_dir, keep_files)

    # assume all files in file_list are in the same directory relative to dirname(installer)
    try:
        for file in os.listdir(installer_dir):
            file = os.path.join(installer_dir, file)
            if os.path.isfile(file) and file not in keep_files:
                logger.info("Deleting file [%s] - not in keep_files", file)
                os.remove(file)

        # walk up and delete empty directories, but stop if the parent is one of the roots used by MG
        # this is just maintenance to prevent aggregating empty directories in cache
        remove_empty_dirs_upwards(installer_dir, installer_root_dirs)
    except BaseException as e:
        logger.error(e)
        return str(e)

    return ""


def is_empty_dir(path):
    return not os.listdir(path)


def remove_empty_dirs_upwards(start_dir, stop_dirs):
    file_dir = start_dir
    while is_empty_dir(file_dir):
        logger.info("Remove now empty sub-directory [%s]", file_dir)
        os.rmdir(file_dir)
        file_dir = os.path.dirname(file_dir)
        if file_dir in stop_dirs:
            break


def postinstaller(game):
    err_msg = ""
    postinst_script = os.path.join(game.install_dir, "support", "postinst.sh")
    if os.path.isfile(postinst_script):
        os.chmod(postinst_script, 0o775)
        stdout, stderr, exitcode = _exe_cmd([postinst_script])
        if exitcode not in [0]:
            err_msg = "Postinstallation script failed: {}".format(postinst_script)
    return err_msg


def uninstall_game(game):
    shutil.rmtree(game.install_dir, ignore_errors=True)
    if os.path.isfile(game.status_file_path):
        os.remove(game.status_file_path)
    path_to_shortcut = os.path.join(APPLICATIONS_DIR, "{}.desktop".format(game.get_stripped_name(to_path=True)))
    if os.path.isfile(path_to_shortcut):
        os.remove(path_to_shortcut)


def _exe_cmd(cmd, print_output=False):
    std_out = ""
    std_err = ""
    done = False
    return_code = None
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, encoding="utf-8"
    )
    os.set_blocking(process.stdout.fileno(), False)
    os.set_blocking(process.stderr.fileno(), False)
    while not done:
        if std_line := process.stdout.readline():
            std_out += std_line
            if print_output:
                print(std_line, end='')

        if err_line := process.stderr.readline():
            std_err += err_line
            if print_output:
                print(err_line, end='')

        # continue the loop until there is
        # 1. a return code and
        # 2. nothing more to consume
        # this makes sure everything was read
        time.sleep(0.02)
        return_code = process.poll()
        line_read = len(std_line) + len(err_line)
        done = return_code is not None and line_read == 0

    process.stdout.close()
    process.stderr.close()

    return std_out, std_err, return_code


def _mv(source_dir, target_dir):
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


# Some installers allow to choose game's language before installation (Divinity Original Sin or XCom EE / XCom 2)
# "--list-languages" option returns "en-US", "fr-FR" etc... for these games.
# Others installers return "French : Français" but disallow to choose game's language before installation
# When outputLogFile is given, the output of --list-languages is also saved in this file to have a bit of
# additional debug information in GH tickets in case the wrong language is picked during installation
def match_game_lang_to_installer(installer: str, language: str, outputLogFile=None):
    if not shutil.which('innoextract'):
        return 'en-US'

    stdout, stderr, ret_code = _exe_cmd(["innoextract", installer, "--list-languages"])
    if ret_code not in [0]:
        logger.error(stderr)
        return "en-US"

    lang_keys = GAME_LANGUAGE_IDS.get(language, [])
    # match lines like ' - french : French'
    # gets the first lowercase word which is the key
    lang_name_regex = re.compile('(\\w+)\\s*:\\s*.*')

    if outputLogFile is not None:
        logger.info('write setup language data: %s', outputLogFile)
        with open(outputLogFile, "w") as text_file:
            text_file.write(stdout)

    for line in stdout.split('\n'):
        if not line.startswith(' -'):
            continue

        lang = line[3:]
        if "-" in lang:  # lang must be like "en-US" only.
            if language == lang[0:2]:
                return lang

        elif match := lang_name_regex.match(lang):
            lang_id = match.group(1)
            if lang_id in lang_keys:
                return lang_id

    return "en-US"
