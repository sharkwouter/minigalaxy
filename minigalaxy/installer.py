import os
import shutil
import shlex
import subprocess
import hashlib
import textwrap

from minigalaxy.config import Config
from minigalaxy.game import Game
from minigalaxy.logger import logger
from minigalaxy.translation import _
from minigalaxy.launcher import get_execute_command
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, APPLICATIONS_DIR
from minigalaxy.wine_utils import get_wine_env, get_wine_path


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
        config: Config
):
    install_dir = config.install_dir
    use_innoextract = True  # not set externally as of yet
    error_message = ""
    tmp_dir = ""
    logger.info("Installing {}".format(game.name))
    try:
        _use_innoextract = use_innoextract and bool(shutil.which('innoextract'))  # single decision point
        if not error_message:
            error_message = verify_installer_integrity(game, installer)
        if not error_message:
            error_message = verify_disk_space(game, installer)
        if not error_message:
            error_message, tmp_dir = make_tmp_dir(game)
        if not error_message:
            error_message = extract_installer(game, installer, tmp_dir, config, _use_innoextract)
        if not error_message:
            error_message = move_and_overwrite(game, tmp_dir, _use_innoextract)
        if not error_message:
            error_message = copy_thumbnail(game)
        if not error_message and config.create_applications_file:
            error_message = create_applications_file(game)
    except Exception:
        logger.error("Error installing game %s", game.name, exc_info=1)
        error_message = _("Unhandled error.")
    _removal_error = remove_installer(game, installer, install_dir, config.keep_installers)
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


def extract_installer(game: Game, installer: str, temp_dir: str, config: Config, use_innoextract=False):
    # Extract the installer
    if game.platform in ["linux"]:
        err_msg = extract_linux(installer, temp_dir)
    else:
        err_msg = extract_windows(game, installer, temp_dir, config, use_innoextract)
    return err_msg


def extract_linux(installer, temp_dir):
    err_msg = ""
    command = ["unzip", "-qq", installer, "-d", temp_dir]
    stdout, stderr, exitcode = _exe_cmd(command)
    if (exitcode not in [0]) and \
       (exitcode not in [1] and "(attempting to process anyway)" not in stderr):
        err_msg = _("The installation of {} failed. Please try again.").format(installer)
    elif len(os.listdir(temp_dir)) == 0:
        err_msg = _("{} could not be unzipped.".format(installer))
    return err_msg


def extract_windows(game: Game, installer: str, temp_dir: str, config: Config, use_innoextract=False):
    # config.windows_installer == 'innoextract' and shutil.which("innoextract")
    err_msg = extract_by_innoextract(installer, temp_dir, config.lang, use_innoextract)
    if err_msg:
        err_msg = extract_by_wine(game, installer, temp_dir, config)
    return err_msg


def extract_by_innoextract(installer: str, temp_dir: str, language: str, use_innoextract: bool):
    err_msg = ""

    if use_innoextract:
        lang = lang_install(installer, language)
        cmd = ["innoextract", installer, "-d", temp_dir, "--gog", lang]
        stdout, stderr, exitcode = _exe_cmd(cmd, False, True)
        if exitcode not in [0]:
            err_msg = _("Innoextract extraction failed.")
        else:
            # In the case the game is installed in "temp_dir/app" like Zeus + Poseidon (Acropolis)
            inno_app_dir = os.path.join(temp_dir, "app")
            if os.path.isdir(inno_app_dir):
                _mv(inno_app_dir, temp_dir)
            # In the case the game is installed in "temp_dir/game" like Dragon Age™: Origins - Ultimate Edition
            inno_game_dir = os.path.join(temp_dir, "game")
            if os.path.isdir(inno_game_dir):
                _mv(inno_game_dir, temp_dir)
            innoextract_unneeded_dirs = ["__redist", "tmp", "commonappdata", "app", "DirectXpackage", "dotNet35"]
            innoextract_unneeded_dirs += ["MSVC2005", "MSVC2005_x64", "support", "__unpacker", "userdocs", "game"]
            for unneeded_dir in innoextract_unneeded_dirs:
                unneeded_dir_full_path = os.path.join(temp_dir, unneeded_dir)
                if os.path.isdir(unneeded_dir_full_path):
                    shutil.rmtree(unneeded_dir_full_path)
    else:
        err_msg = _("Innoextract not installed.")
    return err_msg


def extract_by_wine(game: Game, installer: str, temp_dir: str, config: Config):
    # Set the prefix for Windows games
    prefix_dir = os.path.join(game.install_dir, "prefix")
    game_dir = os.path.join(prefix_dir, "dosdevices", 'c:', 'game')
    wine_env = get_wine_env(game, config)
    wine_bin = get_wine_path(game, config)

    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir, mode=0o755)
        # Creating the prefix before modifying dosdevices
        command = ["env", *wine_env, wine_bin, "wineboot", "-u"]
        stdout, stderr, exitcode = _exe_cmd(command, False, True)
        if exitcode not in [0]:
            return _("Wineprefix creation failed.")

    # calculate relative link from prefix-internal folder to game.install_dir
    # keeping it relative makes sure that the game can be moved around without stuff breaking
    if not os.path.exists(game_dir):
        # 'game' directory itself does not count
        canonical_prefix = os.path.realpath(os.path.join(game_dir, '..'))
        relative = os.path.relpath(game.install_dir, canonical_prefix)
        os.symlink(relative, game_dir)

    installer_args = [
        # use hard-coded directory name within wine, its just a backlink to game.install_dir
        # this avoids issues with varying path and spaces
        "/DIR=c:\\game",
        f"/LANG={config.lang}",
        # capture information for debugging during install
        "/LOG=c:\\install.log",
        "/SAVEINF=c:\\setup.inf",
        '/SILENT'  # installers can run very long, give at least a bit of visual feedback
    ]
    command = ["env", *wine_env, wine_bin, installer, *installer_args]
    stdout, stderr, exitcode = _exe_cmd(command, False, True)
    if exitcode not in [0]:
        linesToWrite = [
            "#!/bin/sh",
            '',
            shlex.join(command)
        ]
        if os.path.exists(game.install_dir):
            #FIXME fix with test somehow, also do the same for prefix creation
            with open(os.path.join(game.install_dir, 'minigalaxy_install_wine_game.sh'), 'w') as f:
                f.writelines(linesToWrite)
        return _("Wine extraction failed.")

    return ""


def move_and_overwrite(game, temp_dir, use_innoextract):
    # Copy the game files into the correct directory
    error_message = ""
    source_dir = (os.path.join(temp_dir, "data", "noarch") if game.platform == 'linux' else
                  temp_dir if use_innoextract else
                  os.path.join(temp_dir, os.path.basename(game.install_dir)))
    target_dir = game.install_dir
    _mv(source_dir, target_dir)

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


def create_applications_file(game):
    error_message = ""
    path_to_shortcut = os.path.join(APPLICATIONS_DIR, "{}.desktop".format(game.get_stripped_name(to_path=True)))
    exe_cmd = shlex.join(get_execute_command(game))
    # Create desktop file definition
    desktop_context = {
        "game_bin_path": exe_cmd,
        "game_name": game.name,
        "game_install_dir": game.install_dir,
        "game_icon_path": os.path.join(game.install_dir, 'support/icon.png')
        }
    desktop_definition = """\
        [Desktop Entry]
        Type=Application
        Terminal=false
        StartupNotify=true
        Exec={game_bin_path}
        Path={game_install_dir}
        Name={game_name}
        Icon={game_icon_path}""".format(**desktop_context)
    if not os.path.isfile(path_to_shortcut):
        try:
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


def remove_installer(game: Game, installer: str, install_dir: str, keep_installers: bool):
    error_message = ""
    installer_directory = os.path.dirname(installer)
    if not os.path.isdir(installer_directory):
        error_message = "No installer directory is present: {}".format(installer_directory)
        return error_message

    if keep_installers:
        keep_dir = os.path.join(install_dir, "installer")
        keep_dir2 = os.path.join(keep_dir, game.get_install_directory_name())
        if keep_dir2 == installer_directory:
            # We are using the keep installer already
            return error_message

        if not compare_directories(installer_directory, keep_dir2):
            shutil.rmtree(keep_dir2, ignore_errors=True)
            try:
                shutil.move(installer_directory, keep_dir2)
            except Exception as e:
                error_message = str(e)
    else:
        for file in os.listdir(installer_directory):
            os.remove(os.path.join(installer_directory, file))

    return error_message


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


def _exe_cmd(cmd, capture_output=True, print_output=False):
    print(f'executing command: {" ".join(cmd)}')
    std_out = []
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               bufsize=1, universal_newlines=True, encoding="utf-8")
    rc = process.poll()
    while rc is None:
        out_line = process.stdout.readline()
        if capture_output and out_line != '':
            std_out.append(out_line)

        if print_output:
            print(out_line, end='')

        rc = process.poll()

    print('command finished, read remaining output (if any)')
    for line in process.stdout.readlines():
        std_out.append(line)

    process.stdout.close()

    output = ''.join(std_out)
    return output, output, rc


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
def lang_install(installer: str, language: str):
    languages = []
    arg = ""
    stdout, stderr, ret_code = _exe_cmd(["innoextract", installer, "--list-languages"])

    for line in stdout.split('\n'):
        if not line.startswith(' -'):
            continue
        languages.append(line[3:])
    for lang in languages:
        if "-" in lang:  # lang must be like "en-US" only.
            if language == lang[0:2]:
                arg = "--language={}".format(lang)
                break
            else:
                arg = "--language=en-US"
                break
    return arg
