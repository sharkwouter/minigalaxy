import hashlib
import json
import os
import re
import shlex
import subprocess
import shutil
import sys
import textwrap
import time

from collections import deque
from enum import Enum, auto
from queue import Empty
from threading import Thread, RLock

from minigalaxy.config import Config
from minigalaxy.constants import GAME_LANGUAGE_IDS
from minigalaxy.file_info import FileInfo
from minigalaxy.game import Game
from minigalaxy.logger import logger
from minigalaxy.translation import _
from minigalaxy.launcher import get_execute_command, get_wine_path, wine_restore_game_link
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, APPLICATIONS_DIR, WINE_RES_PATH, DOWNLOAD_DIR


INSTALL_QUEUE = None


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


def enqueue_game_install(install_id, result_callback, *args, **kwargs):
    global INSTALL_QUEUE
    if not INSTALL_QUEUE:
        INSTALL_QUEUE = InstallerQueue()

    task = InstallTask(install_id, result_callback, *args, **kwargs)
    INSTALL_QUEUE.put(task)


def install_game(  # noqa: C901
        game: Game,
        installer: str,
        language: str,
        install_dir: str,
        keep_installers: bool,
        create_desktop_file: bool,
        installer_inventory=None,
        raise_error=False,
        progress_callback=None
):
    error_message = ""
    error = None
    tmp_dir = ""
    logger.info("Installing {}".format(game.name))

    try:
        if not installer_inventory:
            installer_inventory = InstallerInventory.from_file_system(installer)

        verify_installer_integrity(game, installer_inventory, progress_callback)

        progress_callback(InstallResultType.INSTALL_START, game.name)
        fail_on_error(verify_disk_space(game, installer), InstallResultType.FAILURE)

        tmp_dir, = fail_on_error(make_tmp_dir(game))

        installed_to_tmp, = fail_on_error(extract_installer(game, installer, tmp_dir, language))

        fail_on_error(move_and_overwrite(game, tmp_dir, installed_to_tmp))
        fail_on_error(copy_thumbnail(game))

        fail_on_error(postinstaller(game), InstallResultType.POST_INSTALL_FAILURE)

        if create_desktop_file:
            fail_on_error(create_applications_file(game))

        # Remove at end, but only on success. Allows retries without re-download
        fail_on_error(remove_installer(game, installer, install_dir,
                                       keep_installers, installer_inventory))

    except InstallException as e:
        error = e
        error_message = e.message
        # delete invalid files
        if e.fail_type == InstallResultType.CHECKSUM_ERROR:
            installer_inventory.delete_invalid_files()

    except Exception as e:
        error = InstallException(_("Unhandled error."), data=e)
        error.__cause__ = e
        error_message = error.message

    if error_message:
        logger.error("Error installing game '%s'", game.name, exc_info=error)
        logger.error(error_message)

    if error_message and raise_error:
        if not error:
            error = InstallException(error_message)
        raise error

    return error_message


def fail_on_error(message_to_test, fail_type=None, data=None):
    remaining_args = None
    if isinstance(message_to_test, tuple):
        remaining_args = message_to_test[1:]
        message_to_test = message_to_test[0]

    if message_to_test:
        if not fail_type:
            fail_type = InstallResultType.FAILURE
        if not data and remaining_args:
            data = remaining_args[0]
        raise InstallException(message_to_test, fail_type, data)

    return remaining_args


def verify_installer_integrity(game, installer_inventory, progress_callback=None):
    error_message = []
    invalid_files = {}

    progress_callback(InstallResultType.VERIFY_START, game.name, installer_inventory)
    for installer in installer_inventory.as_keep_files_list():
        installer_file_name = os.path.basename(installer)
        if not os.path.exists(installer):
            error_message = _("{} failed to download.").format(installer_file_name)

        if not installer_inventory.has_checksum(installer_file_name):
            logger.warning("Warning. No info about correct %s MD5 checksum", installer_file_name)
            continue

        hash_md5 = hashlib.md5()
        with open(installer, "rb") as installer_file:
            for chunk in iter(lambda: installer_file.read(8 * 1024), b""):
                hash_md5.update(chunk)
        calculated_checksum = hash_md5.hexdigest()

        if installer_inventory.verify_checksum(installer_file_name, calculated_checksum):
            logger.info("%s integrity is preserved. MD5 is: %s", installer_file_name, calculated_checksum)
            progress_callback(InstallResultType.VERIFY_PROGRESS, installer_file_name, calculated_checksum)
        else:
            error_message.append(_("{} was corrupted. Please download it again.").format(installer_file_name))
            invalid_files[installer] = calculated_checksum

    if error_message:
        raise InstallException('\n'.join(error_message), InstallResultType.CHECKSUM_ERROR, invalid_files)


def verify_disk_space(game, installer):
    err_msg = ""
    if game.platform == "linux":
        required_space = get_game_size_from_unzip(installer)
        if not check_diskspace(required_space, game.install_dir):
            err_msg = _("Not enough space to extract game. Required: {} Available: {}")\
                .format(required_space, get_available_disk_space(game.install_dir))
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


def remove_installer(game: Game, installer: str, keep_installers_dir: str, keep_installers: bool, inventory=None):
    installer_dir = os.path.dirname(installer)
    if not os.path.isdir(installer_dir):
        error_message = "No installer directory is present: {}".format(installer_dir)
        return error_message

    installer_root_dirs = [
        os.path.realpath(DOWNLOAD_DIR),
        keep_installers_dir
    ]

    if not inventory:
        inventory = InstallerInventory.from_file_system(installer)

    logger.info("Cleaning [%s] - keep_installers:%s", installer_dir, keep_installers)

    try:
        inventory.delete_others()
        if not keep_installers:
            inventory.delete_files()

        # walk up and delete empty directories, but stop if the parent is one of the roots used by MG
        # this is just maintenance to prevent aggregating empty directories in cache
        remove_empty_dirs_upwards(installer_dir, installer_root_dirs)
    except Exception as e:
        logger.error("Error while removing installer", exc_info=e)
        return str(e)

    return ""


def safe_delete(file_list):
    """Tries to delete the given files without throwing exceptions where possible."""
    logger.info("Trying to safely delete: %s", file_list)
    for f in file_list:
        if is_empty_dir(f):
            os.rmdir(f)
        elif os.path.isfile(f):
            os.remove(f)


def is_empty_dir(path):
    return os.path.isdir(path) and not os.listdir(path)


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


class InstallerInventory:
    '''Helper class to keep track of completeness of installer downloads'''

    def __init__(self, installer_path=None):
        self.inventory_file = None
        if installer_path:
            self.set_path_once(installer_path)

    @staticmethod
    def from_file_system(installer_path):
        """
        Helper utility to build an instance of InstallerInventory from files in the same directory
        that belong to the given installer_path.
        Expects the following naming convention:
        - game_installer_version.[exe|sh]
        - game_installer_version-1.bin
        - game_installer_version-2.bin ...

        The inventory will contain all files whose names are matching
        the base name of the installer (without extension) in the SAME directory.
        No recursion.

        This is a fallback for games that have been downloaded before InstallerInventory was introduced.
        Files added like this won't have checksums and the is_complete check makes little sense.
        """
        inventory = InstallerInventory(installer_path)
        if os.path.isfile(inventory.inventory_file):
            return inventory

        # if the file doesn't exist, populate from disk to get names at the very least
        for f in os.listdir(inventory.directory):
            fullpath = os.path.join(inventory.directory, f)
            if os.path.isfile(fullpath) and f.startswith(inventory.name_prefix):
                inventory.add_file(f, FileInfo(size=InstallerInventory.size_of(fullpath)))

        return inventory

    @staticmethod
    def size_of(file):
        return os.stat(file).st_size

    def set_path_once(self, installer_path=None):
        if not self.inventory_file and installer_path:
            self.directory = os.path.dirname(installer_path)
            self.name_prefix = os.path.basename(os.path.splitext(installer_path)[0])
            self.inventory_file = os.path.join(self.directory, f"{self.name_prefix}.json")
            self.load()

    def load(self):
        if not os.path.isfile(self.inventory_file):
            self.data = {}
            return self.data

        with open(self.inventory_file, 'r') as inventory:
            self.data = json.load(inventory)

        return self.data

    def save(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory, mode=0o755)

        with open(self.inventory_file, 'w') as inventory_file:
            json.dump(self.data, inventory_file)

    def add_file(self, name, file_info):
        self.data[os.path.basename(name)] = file_info.as_dict()

    def has_checksum(self, file_name):
        return not self.data.get(file_name, {}).get("md5", None) is None

    def verify_checksum(self, file_name, actual_checksum):
        file_info = self.data.get(file_name)
        recorded_checksum = file_info.get("md5", "")
        if recorded_checksum == actual_checksum:
            return True
        else:
            file_info["md5"] = False
            return False

    def get_expected_total_size(self):
        total_size = 0
        for file_data in self.data.values():
            total_size += file_data.get('size', 0)
        return total_size

    def is_complete(self):
        self.load()
        if not self.data:
            return False

        for file in self.data.keys():
            full_path = os.path.join(self.directory, file)
            if not os.path.exists(full_path) or InstallerInventory.size_of(full_path) != self.data[file].get("size", 0):
                return False

        return True

    def as_keep_files_list(self):
        """Returns a list of all files contained in this inventory INCLUDING the inventory itself"""
        files = self.contained_files()
        files.append(self.inventory_file)
        return files

    def contained_files(self):
        files = []
        for f in self.data.keys():
            files.append(os.path.join(self.directory, f))
        return files

    def delete_files(self):
        """delete files which are part of this inventory"""
        file_list = self.as_keep_files_list()
        file_list.append(self.directory)
        safe_delete(file_list)

    def delete_others(self):
        """
        Delete files in the same directory, which are NOT part of this inventory.
        Used to remove previous versions after successful install.
        """
        delete_list = []
        for f in os.listdir(self.directory):
            if os.path.isdir(f):
                continue
            if f not in self.data:
                delete_list.append(f)

        safe_delete(delete_list)

    def delete_invalid_files(self):
        """
        Delete files of this inventory which are flagged as having an invalid checksum.
        Flagging must have happened by calling IntallerInventory.verify_checksum.
        It is advised not to call save() afterwards because that will overwrite the recorded checksums with False
        """
        delete_list = []
        for file, info in self.data.items():
            if info.get("md5", None) is False:
                delete_list.append(os.path.join(self.directory, file))

        safe_delete(delete_list)


class InstallResultType(Enum):
    """checksum verification has started"""
    VERIFY_START = auto()
    """A file has been verified successfully"""
    VERIFY_PROGRESS = auto()
    """The real installation has started"""
    INSTALL_START = auto()
    """Installation ended with success"""
    SUCCESS = auto()
    """Installation ended in failure"""
    FAILURE = auto()
    """Checksum verification failed"""
    CHECKSUM_ERROR = auto()
    """An error happened during post installation actions"""
    POST_INSTALL_FAILURE = auto()


class InstallResult:
    def __init__(self, install_id, result_type: InstallResultType, reason, details=None):
        """Data class that will be passed to result_callback of InstallTask
        reason is a type-dependent string:
        - INSTALL_START: game name
        - VERIFY_START: game name
        - VERIFY_PROGRESS: verified file
        - SUCCESS: install directory path
        - FAILURE and CHECKSUM_ERROR: string error message
        - POST_INSTALL_FAILURE: error message

        the "details" field provides additional context information:
        - VERIFY_START: InstallerInventory
        - VERIFY_PROGRESS: the md5 of the file
        - FAILURE: depending on the failing step, usually a directory path
        - CHECKSUM_ERROR: dict {abs_file: calculated_checksum} of all failed files
        """
        self.install_id = install_id
        self.type = result_type
        self.reason = reason
        self.details = details
        self.installation_terminated = result_type in [
            InstallResultType.SUCCESS,
            InstallResultType.FAILURE,
            InstallResultType.CHECKSUM_ERROR,
            InstallResultType.POST_INSTALL_FAILURE
        ]

    def __str__(self):
        return f"InstallResult(id={self.install_id}, type={self.type}), reason={self.reason})"

    def __eq__(self, other):
        """mainly used for testing, therefore not the most efficient implementation"""
        return str(self) == str(other)


class InstallException(Exception):
    def __init__(self, message, fail_type=InstallResultType.FAILURE, data=None):
        self.fail_type = fail_type
        self.message = message
        self.data = data


class InstallTask:
    def __init__(self, install_id=None, result_callback=None, *args, **kwargs):
        self.game = InstallTask.__locate_game_in_args(*args, **kwargs)
        if not install_id:
            install_id = self.game.id
        if not result_callback or not callable(result_callback):
            raise ValueError("result_callback is required")
        self.installer_id = install_id
        self.title = InstallTask.get_title_for_id(self.game, install_id)
        self.callback = result_callback
        self.arg_array = args
        self.named_args = kwargs

    def execute(self):
        try:
            # install_game will throw an exception if it doesn't succeed
            install_game(*self.arg_array, **self.named_args, raise_error=True, progress_callback=self.notifyStep)
            self.notifyStep(InstallResultType.SUCCESS, self.game.install_dir, None)
        except InstallException as e:
            logger.error("Error installing item %s: %s", self.installer_id, e.message, exc_info=1)
            self.notifyStep(e.fail_type, e.message, e.data)

    def notifyStep(self, result_type: InstallResultType, reason='', details=None):
        '''Small proxy method to be passed to install_game for intermediate progress report'''
        try:
            self.callback(InstallResult(self.installer_id, result_type, reason, details))
        except Exception as e:
            logger.error("Installation callback handler threw an error: %s", e.message, exc_info=1)

    def __eq__(self, other):
        if not isinstance(other, InstallTask):
            return False
        return self.installer_id == other.installer_id and self.arg_array == other.arg_array

    def __str__(self):
        return f"InstallTask(id={self.installer_id}, args={self.arg_array}, kwargs={str(self.named_args)})"

    @staticmethod
    def __locate_game_in_args(*args, **kwargs):
        for a in [*args, *kwargs.values()]:
            if isinstance(a, Game):
                return a
        raise ValueError("No instance of Game in InstallTask constructor arguments")

    @staticmethod
    def get_title_for_id(game: Game, item_id):
        if game.id == item_id:
            return game.name
        else:
            for dlc in game.dlcs:
                if dlc.get('id') == item_id:
                    return dlc.get('title')
        # this normally shouldn't happen and would mean that an
        # id was passed which is not in the dlc list
        return game.name


class InstallerQueue:
    """
    Special queue which includes a worker thread to handle game installations.
    The worker will only be started and active while there are items in the queue.
    Custom implementation is chosen because ThreadPoolExecutors don't auto-stop
    and regular Queues don't provide a check for contained items aside from iterating through everything.
    """

    def __init__(self, lock_to_use=RLock()):
        self.queue = deque()
        self.worker = None
        self.active_item = None
        self.state_lock = lock_to_use

    def get(self):
        with self.state_lock:
            if not self.queue:
                raise Empty
            return self.queue.popleft()

    def put(self, item):
        """
        Puts the given item into the queue, if it is not contained (or in work) already.
        Returns True if the item was added, False otherwise.
        (Re)starts the internally managed installation task worker thread if the item was put into to queue.
        """
        with self.state_lock:
            if self.active_item == item or item in self.queue:
                return False
            logger.debug("Queuing: %s", item)
            self.queue.append(item)
            if not self.worker or not self.worker.is_alive():
                self.worker = Thread(name="InstallerQueue worker", target=self.__install_queued_items)
                self.worker.start()
            return True

    def clear(self):
        with self.state_lock:
            self.queue.clear()

    def is_active(self):
        with self.state_lock:
            return self.active_item and self.worker.is_alive()

    def is_empty(self):
        with self.state_lock:
            return len(self.queue) == 0

    def shutdown(self):
        """
        Empties the queue. Will not cancel an actively running installation.
        Returns the active item, if any. None otherwise.
        """
        with self.state_lock:
            self.clear()
            return self.active_item

    def __install_queued_items(self):
        logger.debug("Starting installer thread")
        is_empty = self.is_empty()
        try:
            while not is_empty:
                with self.state_lock:
                    self.active_item = self.get()
                self.active_item.execute()
                with self.state_lock:
                    self.active_item = None
                is_empty = self.is_empty()
        except Empty:
            pass

        with self.state_lock:
            self.active_item = None
            self.worker = None
        logger.debug("Stopping installer thread")
