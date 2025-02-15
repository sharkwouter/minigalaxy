import os
import shutil
import threading
import time
import urllib.parse

from minigalaxy.download import Download, DownloadType
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.installer import uninstall_game, install_game, check_diskspace
from minigalaxy.launcher import start_game
from minigalaxy.logger import logger
from minigalaxy.paths import THUMBNAIL_DIR, UI_DIR
from minigalaxy.translation import _
from minigalaxy.ui.gtk import Gtk, GLib, Notify
from minigalaxy.ui.library_entry import LibraryEntry


@Gtk.Template.from_file(os.path.join(UI_DIR, "gametile.ui"))
class GameTile(LibraryEntry, Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    wine_icon = Gtk.Template.Child()
    update_icon = Gtk.Template.Child()
    menu_button_update = Gtk.Template.Child()
    menu_button_dlc = Gtk.Template.Child()
    menu_button_uninstall = Gtk.Template.Child()
    dlc_horizontal_box = Gtk.Template.Child()
    menu_button_information = Gtk.Template.Child()
    menu_button_properties = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()

    def __init__(self, parent_library, game: Game):
        super().__init__(parent_library, game)
        Gtk.Frame.__init__(self)

        self.init_ui_elements()

    # Downloads if Minigalaxy was closed with this game downloading
    def resume_download_if_expected(self):
        download_ids = self.config.current_downloads
        if self.game.id in download_ids and self.current_state == State.DOWNLOADABLE:
            download_thread = threading.Thread(target=self.__download_game)
            download_thread.start()

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        dont_act_in_states = [State.QUEUED, State.DOWNLOADING, State.INSTALLING, State.UNINSTALLING]
        err_msg = ""
        if self.current_state in dont_act_in_states:
            pass
        elif self.current_state in [State.INSTALLED, State.UPDATABLE]:
            err_msg = start_game(self.game)
        elif self.current_state == State.INSTALLABLE:
            install_thread = threading.Thread(target=self.__install_game, args=(self.get_keep_executable_path(),))
            install_thread.start()
        elif self.current_state == State.DOWNLOADABLE:
            download_thread = threading.Thread(target=self.__download_game)
            download_thread.start()
        if err_msg:
            self.parent_window.show_error(_("Failed to start {}:").format(self.game.name), err_msg)

    @Gtk.Template.Callback("on_menu_button_information_clicked")
    def show_information(self, button):
        super().show_information(button)

    @Gtk.Template.Callback("on_menu_button_properties_clicked")
    def show_properties(self, button):
        super().show_properties(button)

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def on_button_cancel(self, widget):
        question = _("Are you sure you want to cancel downloading {}?").format(self.game.name)
        if self.parent_window.show_question(question):
            self.prevent_resume_on_startup()
            self.download_manager.cancel_download(self.download_list)
            try:
                for filename in os.listdir(self.download_dir):
                    if self.game.get_install_directory_name() in filename:
                        os.remove(os.path.join(self.download_dir, filename))
            except FileNotFoundError:
                pass

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        question = _("Are you sure you want to uninstall %s?" % self.game.name)
        if self.parent_window.show_question(question):
            uninstall_thread = threading.Thread(target=self.__uninstall_game)
            uninstall_thread.start()

    @Gtk.Template.Callback("on_menu_button_update_clicked")
    def on_menu_button_update(self, widget):
        download_thread = threading.Thread(target=self.__download_update)
        download_thread.start()

    def load_thumbnail(self):
        set_result = self.__set_image("")
        if not set_result:
            tries = 10
            performed_try = 0
            while performed_try < tries:
                if self.game.image_url and self.game.id:
                    # Download the thumbnail
                    image_url = "https:{}_196.jpg".format(self.game.image_url)
                    thumbnail = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
                    download = Download(image_url, thumbnail, DownloadType.THUMBNAIL,
                                        finish_func=self.__set_image)
                    self.download_manager.download_now(download)
                    set_result = True
                    break
                performed_try += 1
                time.sleep(1)
        return set_result

    def __set_image(self, save_location):
        set_result = False
        self.game.set_install_dir(self.config.install_dir)
        thumbnail_install_dir = os.path.join(self.game.install_dir, "thumbnail.jpg")
        if os.path.isfile(thumbnail_install_dir):
            GLib.idle_add(self.image.set_from_file, thumbnail_install_dir)
            set_result = True
        elif save_location and os.path.isfile(save_location):
            GLib.idle_add(self.image.set_from_file, save_location)
            # Copy image to
            if os.path.isdir(os.path.dirname(thumbnail_install_dir)):
                shutil.copy2(save_location, thumbnail_install_dir)
            set_result = True
        thumbnail_path = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
        if os.path.isfile(thumbnail_path):
            GLib.idle_add(self.image.set_from_file, thumbnail_path)
            set_result = True
        return set_result

    def __download_game(self) -> None:
        finish_func = self.__install_game
        cancel_to_state = State.DOWNLOADABLE
        result, download_info = self.get_download_info()
        if result:
            result = self.__download(download_info, DownloadType.GAME, finish_func,
                                     cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __download(self, download_info, download_type, finish_func, cancel_to_state):  # noqa: C901
        download_success = True
        self.game.set_install_dir(self.config.install_dir)
        GLib.idle_add(self.update_to_state, State.QUEUED)

        # Need to update the config with DownloadType metadata
        current_download_ids = self.config.current_downloads
        if current_download_ids is None:
            current_download_ids = set()
        else:
            current_download_ids = set(current_download_ids)
        current_download_ids.add(self.game.id)
        self.config.current_downloads = list(current_download_ids)
        # Start the download for all files
        self.download_list = []
        number_of_files = len(download_info['files'])
        total_file_size = 0
        download_files = []
        self.download_finished = 0

        def finish_func_wrapper(func):
            def wrapper(*args):
                self.download_finished += 1
                if self.download_finished == number_of_files:
                    # Assume the first item in download_info['files] is the executable
                    # This item ends up last in self.download_list because it's reversed
                    finish_func(self.download_list[-1].save_location)

            if func is not None:
                return wrapper
            else:
                return None

        for key, file_info in enumerate(download_info['files']):
            try:
                download_url = self.api.get_real_download_link(file_info["downlink"])
            except ValueError as e:
                logger.error("Error getting download URL from file_info downlink: %s", file_info["downlink"], exc_info=1)
                GLib.idle_add(self.parent_window.show_error, _("Download error"), _(str(e)))
                download_success = False
                break
            info = self.api.get_download_file_info(file_info["downlink"])
            total_file_size += info.size
            # Extract the filename from the download url
            filename = urllib.parse.unquote(urllib.parse.urlsplit(download_url).path)
            filename = filename.split("/")[-1]
            download_path = os.path.join(self.download_dir, filename)
            if info.md5:
                self.game.md5sum[os.path.basename(download_path)] = info.md5
            download = Download(
                url=download_url,
                save_location=download_path,
                download_type=DownloadType.GAME,
                finish_func=finish_func_wrapper(finish_func),
                progress_func=self.set_progress,
                cancel_func=lambda: self.__cancel(to_state=cancel_to_state),
                number=number_of_files - key,
                out_of_amount=number_of_files,
                game=self.game
            )
            download_files.insert(0, download)
        self.download_list.extend(download_files)

        if check_diskspace(total_file_size, self.game.install_dir):
            self.download_manager.download(download_files)
            ds_msg_title = ""
            ds_msg_text = ""
        else:
            ds_msg_title = "Download error"
            ds_msg_text = "Not enough disk space to install game."
            download_success = False
        if ds_msg_title:
            GLib.idle_add(self.parent_window.show_error, _(ds_msg_title), _(ds_msg_text))
        return download_success

    def __install_game(self, save_location):
        if self.game.id in self.config.current_downloads:
            self.config.current_downloads.remove(self.game.id)
        self.download_list = []
        self.game.set_install_dir(self.config.install_dir)
        install_success = self.__install(save_location)
        if install_success:
            popup = Notify.Notification.new("Minigalaxy", _("Finished downloading and installing {}")
                                            .format(self.game.name), "dialog-information")
            popup.show()
            self._check_for_dlc(self.api.get_info(self.game))

    def __install(self, save_location, update=False, dlc_title=""):
        if update:
            processing_state = State.UPDATING
            failed_state = State.INSTALLED
        else:
            processing_state = State.INSTALLING
            failed_state = State.DOWNLOADABLE
        success_state = State.INSTALLED
        GLib.idle_add(self.update_to_state, processing_state)
        err_msg = install_game(
            self.game,
            save_location,
            self.config.lang,
            self.config.install_dir,
            self.config.keep_installers,
            self.config.create_applications_file
        )
        if not err_msg:
            GLib.idle_add(self.update_to_state, success_state)
            install_success = True
            if dlc_title:
                self.game.set_dlc_info("version", self.api.get_version(self.game, dlc_name=dlc_title), dlc_title)
            else:
                self.game.set_info("version", self.api.get_version(self.game))
        else:
            GLib.idle_add(self.parent_window.show_error, _("Failed to install {}").format(self.game.name), err_msg)
            GLib.idle_add(self.update_to_state, failed_state)
            install_success = False
        return install_success

    def __cancel(self, to_state):
        self.download_list = []
        GLib.idle_add(self.update_to_state, to_state)
        GLib.idle_add(self.reload_state)

    def __download_update(self) -> None:
        finish_func = self.__update
        cancel_to_state = State.UPDATABLE
        result, download_info = self.get_download_info(self.game.platform)
        if result:
            result = self.__download(download_info, DownloadType.GAME_UPDATE, finish_func,
                                     cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __update(self, save_location):
        install_success = self.__install(save_location, update=True)
        if install_success:
            if self.game.platform == "windows":
                self.image.set_tooltip_text("{} (Wine)".format(self.game.name))
            else:
                self.image.set_tooltip_text(self.game.name)
        for dlc in self.game.dlcs:
            download_info = self.api.get_download_info(self.game, dlc_installers=dlc["downloads"]["installers"])
            if self.game.is_update_available(version_from_api=download_info["version"], dlc_title=dlc["title"]):
                self.__download_dlc(dlc["downloads"]["installers"])

    def __download_dlc(self, dlc_installers) -> None:
        def finish_func(save_location):
            self.__install_dlc(save_location, dlc_title=dlc_title)

        download_info = self.api.get_download_info(self.game, dlc_installers=dlc_installers)
        dlc_title = self.game.name
        for dlc in self.game.dlcs:
            if dlc["downloads"]["installers"] == dlc_installers:
                dlc_title = dlc["title"]
        cancel_to_state = State.INSTALLED
        result = self.__download(download_info, DownloadType.GAME_DLC, finish_func,
                                 cancel_to_state)
        if not result:
            GLib.idle_add(self.update_to_state, cancel_to_state)

    def __install_dlc(self, save_location, dlc_title):
        install_success = self.__install(save_location, dlc_title=dlc_title)
        if not install_success:
            GLib.idle_add(self.update_to_state, State.INSTALLED)
        self._check_for_update_dlc()

    def update_gtk_box_for_dlc(self, dlc_id, icon, title, installer):
        if title not in self.dlc_dict:
            dlc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            dlc_box.set_spacing(8)
            image = Gtk.Image()
            image.set_from_icon_name("media-optical", Gtk.IconSize.BUTTON)
            dlc_box.pack_start(image, False, True, 0)
            label = Gtk.Label(label=title, xalign=0)
            dlc_box.pack_start(label, True, True, 0)
            install_button = Gtk.Button()
            dlc_box.pack_start(install_button, False, True, 0)
            self.dlc_dict[title] = [install_button, image]
            self.dlc_dict[title][0].connect("clicked", self.__dlc_button_clicked, installer)
            self.dlc_horizontal_box.pack_start(dlc_box, False, True, 0)
            dlc_box.show_all()
            self.get_async_image_dlc_icon(dlc_id, image, icon, title)
        download_info = self.api.get_download_info(self.game, dlc_installers=installer)
        if self.game.is_update_available(version_from_api=download_info["version"], dlc_title=title):
            icon_name = "emblem-synchronizing"
            self.dlc_dict[title][0].set_sensitive(True)
        elif self.game.is_installed(dlc_title=title):
            icon_name = "object-select"
            self.dlc_dict[title][0].set_sensitive(False)
        else:
            icon_name = "document-save"
            if not self.download_list:
                self.dlc_dict[title][0].set_sensitive(True)
        install_button_image = Gtk.Image()
        install_button_image.set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        self.dlc_dict[title][0].set_image(install_button_image)

    def __dlc_button_clicked(self, button, installer):
        button.set_sensitive(False)
        threading.Thread(target=self.__download_dlc, args=(installer,)).start()

    def __uninstall_game(self):
        GLib.idle_add(self.update_to_state, State.UNINSTALLING)
        uninstall_game(self.game)
        GLib.idle_add(self.update_to_state, State.DOWNLOADABLE)
        GLib.idle_add(self.reload_state)

    def state_installed(self):
        self.menu_button.get_style_context().add_class("suggested-action")
        super().state_installed()

    def state_uninstalling(self):
        self.menu_button.get_style_context().remove_class("suggested-action")
        super().state_uninstalling()
