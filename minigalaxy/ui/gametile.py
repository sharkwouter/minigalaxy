import shutil
import zipfile
import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
import requests
import json
import os
import webbrowser
import threading
import subprocess
from minigalaxy.translation import _
from minigalaxy.paths import CACHE_DIR, THUMBNAIL_DIR, UI_DIR

@Gtk.Template.from_file(os.path.join(UI_DIR, "gametile.ui"))
class GameTile(Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    menu_button_os = Gtk.Template.Child()

    def __init__(self, parent, game=None, api=None, install_dir=""):
        Gtk.Frame.__init__(self)
        self.parent = parent
        self.game = game
        self.api = api
        self.progress_bar = None
        self.installed = False
        self.install_dir = install_dir
        self.busy = False

        # Set the os version for each games at launch
        self.api.get_os_game(self.game)

        self.image.set_tooltip_text(self.game.name)

        # Set folder for download installer
        self.download_dir = os.path.join(CACHE_DIR, "download")

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(self.api.config.get("install_dir"), "installer")

        # Set the prefix for Windows games
        self.prefix_dir = os.path.join(self.api.config.get("install_dir"), "prefix")

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        self.load_state()

        image_thread = threading.Thread(target=self.__load_image)
        image_thread.start()

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        if self.busy:
            return
        if self.installed:
            self.__start_game()
        else:
            self.busy = True
            self.__create_progress_bar()
            widget.set_sensitive(False)
            widget.set_label(_("downloading..."))
            download_thread = threading.Thread(target=self.__download_file)
            download_thread.start()

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        message_dialog = Gtk.MessageDialog(parent=self.parent,
                                           flags=Gtk.DialogFlags.MODAL,
                                           message_type=Gtk.MessageType.WARNING,
                                           buttons=Gtk.ButtonsType.OK_CANCEL,
                                           message_format=_("Are you sure to uninstall %s" % self.game.name))
        response = message_dialog.run()

        if response == Gtk.ResponseType.OK:
            self.menu_button.hide()
            self.button.set_sensitive(False)
            self.button.set_label(_("uninstalling.."))
            uninstall_thread = threading.Thread(target=self.__uninstall_game)
            uninstall_thread.start()
            message_dialog.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            message_dialog.destroy()

    @Gtk.Template.Callback("on_menu_button_open_clicked")
    def on_menu_button_open_files(self, widget):
        subprocess.call(["xdg-open", self.__get_install_dir()])

    @Gtk.Template.Callback("on_menu_button_support_clicked")
    def on_menu_button_support(self, widget):
        try:
            webbrowser.open(self.api.get_info(self.game)['links']['support'], new=2)
        except:
            dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.ERROR,
                parent=self.parent,
                modal=True,
                buttons=Gtk.ButtonsType.OK,
                text=_("Couldn't open support page")
            )
            dialog.format_secondary_text(_("Please check your internet connection"))
            dialog.run()
            dialog.destroy()

    @Gtk.Template.Callback("on_menu_button_os_Windows_clicked")
    def on_menu_button_os_version_Win(self, widget):
        os_dialog_Win = Gtk.MessageDialog(
                message_type=Gtk.MessageType.WARNING,
                modal=True,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text=_("Install the Windows version for this game ?")
        )

        response = os_dialog_Win.run()

        if response == Gtk.ResponseType.OK:
            self.api.config.set("os_version_" + str(self.game.id), "windows")
            if os.path.exists(self.__keep_install_path()):
                self.button.set_label(_("install"))
            os_dialog_Win.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            os_dialog_Win.destroy()

    def __keep_install_path(self):
        if self.api.config.get('os_version_' + str(self.game.id)) == "linux":
            self.keep_path = os.path.join(self.keep_dir, '{}.sh'.format(self.game.name))
            return self.keep_path
        elif self.api.config.get('os_version_' + str(self.game.id)) == "windows":
            self.keep_path = os.path.join(self.keep_dir, "{}.exe".format(self.game.name))
            return self.keep_path

    def __download_path(self):
        if self.api.config.get('os_version_' + str(self.game.id)) == "linux":
            self.download_path = os.path.join(self.download_dir, '{}.sh'.format(self.game.name))
            return self.download_path
        elif self.api.config.get('os_version_' + str(self.game.id)) == "windows":
            self.download_path = os.path.join(self.download_dir, "{}.exe".format(self.game.name))
            return self.download_path

    def __load_image(self) -> None:
        image_thumbnail_dir = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
        image_install_dir = os.path.join(self.__get_install_dir(), "thumbnail.jpg")

        # Set the image to the one in the game directory in offline mode
        if self.game.id == 0:
            if os.path.isfile(image_install_dir):
                GLib.idle_add(self.image.set_from_file, image_install_dir)
            return

        # Download the image if it doesn't exist yet
        if not os.path.isfile(image_thumbnail_dir):
            image_url = "https:{}_196.jpg".format(self.game.image_url)
            download = requests.get(image_url)
            with open(image_thumbnail_dir, "wb") as writer:
                writer.write(download.content)
                writer.close()

        # Copy the image to the game directory if not there yet
        if not os.path.isfile(image_install_dir) and os.path.isdir(self.__get_install_dir()):
            shutil.copy2(image_thumbnail_dir, image_install_dir)

        GLib.idle_add(self.image.set_from_file, image_thumbnail_dir)

    def __download_file(self) -> None:
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        if not os.path.exists(self.__keep_install_path()):
            download_info = self.api.get_download_info(self.game)
            file_url = download_info["downlink"]
            data = requests.get(file_url, stream=True)
            handler = open(self.__download_path(), "wb")

            total_size = int(data.headers.get('content-length'))
            downloaded_size = 0
            chunk_count = 0
            for chunk in data.iter_content(chunk_size=4096):
                if chunk:
                    chunk_count += 1
                    handler.write(chunk)
                    downloaded_size += len(chunk)
                    # Only update the progress bar every 2 megabytes
                    if chunk_count == 4000:
                        percentage = downloaded_size / total_size
                        GLib.idle_add(self.progress_bar.set_fraction, percentage)
                        chunk_count = 0
            handler.close()

        GLib.idle_add(self.progress_bar.destroy)
        GLib.idle_add(self.button.set_label, _("installing.."))
        self.__install_game()
        self.busy = False
        GLib.idle_add(self.load_state)
        GLib.idle_add(self.button.set_sensitive, True)
        GLib.idle_add(self.parent.filter_library)

    def __install_game(self) -> None:
        # Make a temporary empty directory for extracting the installer
        temp_dir = os.path.join(CACHE_DIR, "extract/{}".format(self.game.id))
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir)

        # Extract the installer
        if os.path.exists(self.__download_path()):
            installer_path = self.__download_path()
        else:
            installer_path = self.__keep_install_path()

        # Make sure the install directory exists
        library_dir = self.api.config.get("install_dir")
        if not os.path.exists(library_dir):
            os.makedirs(library_dir)

        if installer_path.endswith('.sh'):
            with zipfile.ZipFile(installer_path) as archive:
                for member in archive.namelist():
                    file = archive.getinfo(member)
                    archive.extract(file, temp_dir)
                    # Set permissions
                    attr = file.external_attr >> 16
                    os.chmod(os.path.join(temp_dir, member), attr)

            shutil.move(os.path.join(temp_dir, "data/noarch"), self.__get_install_dir())
        elif installer_path.endswith('.exe'):
            if shutil.which("wine"):
                if not os.path.exists(self.prefix_dir):
                    os.makedirs(self.prefix_dir)

                prefix = os.path.join(self.prefix_dir, self.game.name)
                os.environ["WINEPREFIX"] = prefix

                # It's possible to set install dir as argument before installation
                command = [shutil.which("wine"), installer_path, "/dir=" + self.__get_install_dir(), "/verysilent", "/NORESTART", "/CLOSEAPPLICATIONS"]
                subprocess.run(command)

        shutil.copyfile(
            os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id)),
            os.path.join(self.__get_install_dir(), "thumbnail.jpg"),
        )

        # Remove the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        if self.api.config.get("keep_installers"):
            if not os.path.exists(self.keep_dir):
                os.makedirs(self.keep_dir)
            if not os.path.exists(self.__keep_install_path()):
                os.rename(self.__download_path(),self.__keep_install_path())
        else:
            os.remove(self.__download_path())

    def __uninstall_game(self):
        shutil.rmtree(self.__get_install_dir(), ignore_errors=True)
        # Delete the prefix for the windows game
        if os.path.join(self.prefix_dir, self.game.name):
            shutil.rmtree(os.path.join(self.prefix_dir, self.game.name), ignore_errors=True)
        GLib.idle_add(self.load_state)
        GLib.idle_add(self.button.set_sensitive, True)

    def __create_progress_bar(self) -> None:
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_halign(Gtk.Align.CENTER)
        self.progress_bar.set_size_request(196, -1)
        self.progress_bar.set_hexpand(False)
        self.progress_bar.set_vexpand(False)
        self.set_center_widget(self.progress_bar)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.show_all()

    def __get_install_dir(self):
        if not self.install_dir or not os.path.isdir(self.install_dir):
            self.install_dir = os.path.join(self.api.config.get("install_dir"), self.game.name)
        return self.install_dir

    def menu_os(self):
        if self.api.config.get("os_version_" + str(self.game.id)) == "linux":
            self.menu_button_os.show()

    def load_state(self) -> None:
        if self.busy:
            return
        if os.path.isfile(os.path.join(self.__get_install_dir(), "thumbnail.jpg")):
            self.installed = True
            self.image.set_sensitive(True)
            self.button.set_label(_("play"))
            self.menu_button.show()
            self.menu_button_os.hide()
        elif os.path.exists(self.__keep_install_path()):
            self.installed = False
            self.image.set_sensitive(False)
            self.button.set_label(_("install"))
            self.menu_button.hide()
            self.menu_button_os.show()
        else:
            self.installed = False
            self.image.set_sensitive(False)
            self.button.set_label(_("download"))
            self.menu_button.hide()
            self.menu_os()

    def __start_game(self) -> subprocess:
        error_message = ""
        process = None

        # Change the directory to the install dir
        working_dir = os.getcwd()
        os.chdir(self.__get_install_dir())
        try:
            process = subprocess.Popen(self.__get_execute_command(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            error_message = _("No executable was found in {}").format(self.install_dir)

        # restore the working directory
        os.chdir(working_dir)

        # Check if the application has started and see if it is still runnning after a short timeout
        if process:
            try:
                process.wait(timeout=float(3))
            except subprocess.TimeoutExpired:
                return process
        elif not error_message:
            error_message = _("Couldn't start subprocess")

        # Set the error message to what's been received in std error if not yet set
        if not error_message:
            stdout, stderror = process.communicate()
            error_message = stderror.decode("utf-8")
            stdout_message = stdout.decode("utf-8")
            if not error_message:
                if stdout:
                    error_message = stdout_message
                else:
                    error_message = _("No error message was returned")

        # Show the error as both a dialog and in the terminal
        error_text = _("Failed to start {}:").format(self.game.name)
        print(error_text)
        print(error_message)
        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.ERROR,
            parent=self.parent,
            modal=True,
            buttons=Gtk.ButtonsType.CLOSE,
            text=error_text
        )
        dialog.format_secondary_text(error_message)
        dialog.run()
        dialog.destroy()

    def __get_execute_command(self) -> list:
        files = os.listdir(self.__get_install_dir())

        # Dosbox
        if "dosbox" in files and shutil.which("dosbox"):
            for file in files:
                if re.match(r'^dosbox_?([a-z]|[A-Z]|[0-9])+\.conf$', file):
                    dosbox_config = file
                if re.match(r'^dosbox_?([a-z]|[A-Z]|[0-9])+_single\.conf$', file):
                    dosbox_config_single = file
            if dosbox_config and dosbox_config_single:
                print("Using system's dosbox to launch {}".format(self.game.name))
                return ["dosbox", "-conf", dosbox_config, "-conf", dosbox_config_single, "-no-console", "-c", "exit"]

        # ScummVM
        if "scummvm" in files and shutil.which("scummvm"):
            for file in files:
                if re.match(r'^.*\.ini$', file):
                    scummvm_config = file
                    break
            if scummvm_config:
                print("Using system's scrummvm to launch {}".format(self.game.name))
                return ["scummvm", "-c", scummvm_config]

        # Wine
        if shutil.which("wine"):
            prefix = os.path.join(self.prefix_dir, self.game.name)
            os.environ["WINEPREFIX"] = prefix

            # Find game executable file
            goggame_info = os.path.join(self.__get_install_dir(), "goggame-" + str(self.game.id) + ".info")
            if os.path.isfile(goggame_info):
                with open(goggame_info) as info_data:
                    info_dict = json.load(info_data)
                    path_name = info_dict.get("playTasks")
                    filename = path_name[0]["path"]
                return ["wine", filename]
            else:
                filepath = glob.glob(self.__get_install_dir() + '/*.exe')[0]
                filename = os.path.splitext(os.path.basename(filepath))[0] + '.exe'
                return ["wine", filename]

        # None of the above, but there is a start script
        if "start.sh" in files:
            return ["./start.sh"]

        # This is the final resort, applies to FTL
        if "game" in files:
            game_files = os.listdir("game")
            for file in game_files:
                if re.match(r'^goggame-[0-9]*\.info$', file):
                    os.chdir(os.path.join(self.install_dir, "game"))
                    with open(file, 'r') as info_file:
                        info = json.loads(info_file.read())
                        return ["./{}".format(info["playTasks"][0]["path"])]

        # If no executable was found at all, raise an error
        raise FileNotFoundError()

    def __lt__(self, other):
        names = [str(self), str(other)]
        names.sort()
        if names[0] == str(self):
            return True
        return False
