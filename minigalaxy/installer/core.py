import hashlib
import logging
import os
import re
import shlex
import subprocess
import shutil
import textwrap
import time

from collections import deque
from importlib.resources import as_file
from queue import Empty
from threading import Thread, RLock
from typing import Callable

from .inventory import InstallerInventory
from .model import InstallException, InstallResult, InstallResultType

from minigalaxy import Platform
from minigalaxy.config import Config
from minigalaxy.constants import GAME_LANGUAGE_IDS
from minigalaxy.file_utils import get_available_disk_space, make_tmp_dir, remove_empty_dirs_upwards
from minigalaxy.game import Game
from minigalaxy.resources import get_data_file
from minigalaxy.translation import _
from minigalaxy.launcher import get_execute_commands, get_wine_path, wine_restore_game_link
from minigalaxy.paths import THUMBNAIL_DIR, APPLICATIONS_DIR, DOWNLOAD_DIR


INSTALL_QUEUE = None


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


# result_callback should be 'result_callback: Callable[InstallResult]',
# but that is not yet possible due to the file structure
def enqueue_game_install(result_callback, *args, **kwargs):
    global INSTALL_QUEUE
    if not INSTALL_QUEUE:
        INSTALL_QUEUE = InstallerQueue()

    task = InstallTask(result_callback, *args, **kwargs)
    INSTALL_QUEUE.put(task)


def install_game(  # noqa: C901
        game: Game,
        config: Config,
        installer_inventory=None,
        raise_error=False,
        progress_callback=None
):
    installer = installer_inventory.installer_executable
    language = config.lang,
    install_dir = config.install_dir,
    keep_installers = config.keep_installers
    create_desktop_file = config.create_applications_file

    error_message = ""
    error = None
    tmp_dir = ""
    logging.info("Installing %d: %s (%s)", installer_inventory.item_id, game.name, installer)

    try:
        verify_installer_integrity(game, installer_inventory, progress_callback)

        progress_callback(InstallResultType.INSTALL_START, game.name)
        fail_on_error(verify_disk_space(game, installer), InstallResultType.FAILURE)

        tmp_dir = make_tmp_dir(str(game.id), temp_type="extract")

        installed_to_tmp, = fail_on_error(extract_installer(game, installer_inventory, tmp_dir, language))

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
        logging.error("Error installing game '%s'", game.name, exc_info=error)
        logging.error(error_message)

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
    error_messages = []
    invalid_files = {}

    progress_callback(InstallResultType.VERIFY_START, game.name, installer_inventory)
    for installer in installer_inventory.contained_files():
        installer_file_name = os.path.basename(installer)
        if not os.path.exists(installer):
            error_messages.append(_("{} failed to download.").format(installer_file_name))

        if not installer_inventory.has_checksum(installer_file_name):
            logging.warning("Warning. No info about correct %s MD5 checksum", installer_file_name)
            continue

        hash_md5 = hashlib.md5()
        with open(installer, "rb") as installer_file:
            for chunk in iter(lambda: installer_file.read(8 * 1024), b""):
                hash_md5.update(chunk)
        calculated_checksum = hash_md5.hexdigest()

        if installer_inventory.verify_checksum(installer_file_name, calculated_checksum):
            logging.info("%s integrity is preserved. MD5 is: %s", installer_file_name, calculated_checksum)
            progress_callback(InstallResultType.VERIFY_PROGRESS, installer_file_name, calculated_checksum)
        else:
            error_messages.append(_("{} was corrupted. Please download it again.").format(installer_file_name))
            invalid_files[installer] = calculated_checksum

    if error_messages:
        raise InstallException('\n'.join(error_messages), InstallResultType.CHECKSUM_ERROR, invalid_files)


def verify_disk_space(game, installer):
    err_msg = ""
    if game.platform == Platform.LINUX:
        required_space = get_game_size_from_unzip(installer)
        if not check_diskspace(required_space, game.install_dir):
            err_msg = _("Not enough space to extract game. Required: {} Available: {}")\
                .format(required_space, get_available_disk_space(game.install_dir))
    return err_msg


def extract_installer(game: Game, inventory, temp_dir: str, language: str):
    installer = inventory.installer_executable
    # Extract the installer
    if inventory.target_platform in [Platform.LINUX]:
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
    logging.info(f'use {game_lang} for installer')

    return extract_by_wine(game, installer, game_lang), False


def extract_by_wine(game, installer, game_lang, config=Config()):
    # Set the prefix for Windows games
    prefix_dir = os.path.join(game.install_dir, "prefix")
    wine_env = [
        f"WINEPREFIX={prefix_dir}",
        "WINEDLLOVERRIDES=winemenubuilder.exe=d",
        "WINEDEBUG=fixme-all"  # disable a few misleading wine log statements
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
        reg_file_resource = get_data_file("wine_disable_menubuilder.reg")
        with as_file(reg_file_resource) as reg_file:
            command = ["env", *wine_env, wine_bin, "regedit", str(reg_file.resolve())]
            success, code = try_wine_command(command)
            if not success:
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
    success, code = try_wine_command(installer_cmd_basic + installer_args_full)
    # look at the exit codes and runtime behaviour to determine if the second try is needed
    # see https://jrsoftware.org/ishelp/index.php?topic=setupexitcodes
    if not success and code not in [2, 5]:
        # some games will reject the /SILENT flag
        # because they require the user to accept EULA at the beginning
        # Open normal installer as fallback and hope for the best
        logging.error('Unattended install failed. Try install with wizard dialog.')
        success, code = try_wine_command(installer_cmd_basic)

    if code in [2, 5]:  # user decided to cancel
        return _("Installation canceled by user.")
    if not success:
        return _("Wine extraction failed.")

    return ""


def try_wine_command(command_arr):
    logging.debug('trying to run wine command:[%s]', shlex.join(command_arr))
    stdout, stderr, exitcode = _exe_cmd(command_arr, True)
    if exitcode not in [0]:
        logging.error("Wine install failed with exit code: %d", exitcode)
        logging.error(stderr)
        return False, exitcode

    return True, 0


def move_and_overwrite(game, temp_dir, installed_to_tmp):
    # Copy the game files into the correct directory
    error_message = ""
    source_dir = (os.path.join(temp_dir, "data", "noarch") if game.platform == Platform.LINUX else
                  temp_dir)
    target_dir = game.install_dir

    if installed_to_tmp:
        _mv(source_dir, target_dir)
    else:
        logging.info(f'installation of {game.name} did not use temporary directory - nothing to move')

    # Remove the temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    if game.platform in [Platform.WINDOWS] and "unins000.exe" not in os.listdir(game.install_dir):
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
    exe_cmd_list = get_execute_commands(game)[0].command
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

    logging.info("Cleaning [%s] - keep_installers:%s", installer_dir, keep_installers)

    try:
        inventory.delete_others()
        if not keep_installers:
            inventory.delete_files()

        # walk up and delete empty directories, but stop if the parent is one of the roots used by MG
        # this is just maintenance to prevent aggregating empty directories in cache
        remove_empty_dirs_upwards(installer_dir, installer_root_dirs)
    except Exception as e:
        logging.error("Error while removing installer", exc_info=e)
        return str(e)

    return ""


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
        logging.error(stderr)
        return "en-US"

    lang_keys = GAME_LANGUAGE_IDS.get(language, [])
    # match lines like ' - french : French'
    # gets the first lowercase word which is the key
    lang_name_regex = re.compile('(\\w+)\\s*:\\s*.*')

    if outputLogFile is not None:
        logging.info('write setup language data: %s', outputLogFile)
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


class InstallTask:
    """Encapsulates all pieces of information needed to call 'install_game'"""

    def __init__(self, result_callback: Callable[[InstallResult], None] | None = None, *args, **kwargs):
        """The first argument to this constructor must be a progress/result callback for the (async) installation.
        All further arguments are kept in their '*args' / '**kwargs' form to be passed to 'install_game' later.
        InstallTask itself requires the related 'Game' and 'InstallerInventory' instances passed on as well.
        To not make assumptions over the method signature of 'install_game' and the position of these arguments,
        this constructor searched the required instances flexibly in '*args' and '**kwargs'.
        """
        self.game = InstallTask._locate_type_in_args(Game, *args, **kwargs)
        self.installer = InstallTask._locate_type_in_args(InstallerInventory, *args, **kwargs)
        if not result_callback or not callable(result_callback):
            raise ValueError("result_callback is required")
        self.installer_id = self.installer.item_id
        self.title = InstallTask.get_title_for_id(self.game, self.installer_id)
        self.callback = result_callback
        self.arg_array = args
        self.named_args = kwargs

    def execute(self):
        try:
            # install_game will throw an exception if it doesn't succeed
            install_game(*self.arg_array, **self.named_args, raise_error=True, progress_callback=self.notifyStep)
            self.notifyStep(InstallResultType.SUCCESS, self.game.install_dir, None)
        except InstallException as e:
            logging.error("Error installing item %s: %s", self.installer_id, e.message, exc_info=1)
            self.notifyStep(e.fail_type, e.message, e.data)

    def notifyStep(self, result_type: InstallResultType, reason='', details=None):
        '''Small proxy method to be passed to install_game for intermediate progress report'''
        try:
            self.callback(InstallResult(self.installer_id, result_type, reason, details))
        except Exception:
            logging.error("Installation callback handler threw an error:", exc_info=1)

    def __eq__(self, other):
        if not isinstance(other, InstallTask):
            return False
        return self.installer_id == other.installer_id and self.arg_array == other.arg_array

    def __str__(self):
        return f"InstallTask(id={self.installer_id}, args={self.arg_array}, kwargs={str(self.named_args)})"

    @staticmethod
    def _locate_type_in_args(class_type, *args, **kwargs):
        for a in [*args, *kwargs.values()]:
            if isinstance(a, class_type):
                return a
        raise ValueError(f"No instance of {class_type.__name__} in InstallTask constructor arguments")

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
            logging.debug("Queuing: %s", item)
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
        logging.debug("Starting installer thread")
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
        logging.debug("Stopping installer thread")
