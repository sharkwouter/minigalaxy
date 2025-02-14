import os
import threading

from minigalaxy.api import NoDownloadLinkFound
from minigalaxy.download import Download
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.logger import logger
from minigalaxy.paths import CACHE_DIR, DOWNLOAD_DIR, ICON_DIR, ICON_WINE_PATH
from minigalaxy.translation import _
from minigalaxy.ui.gtk import GLib
from minigalaxy.ui.information import Information
from minigalaxy.ui.properties import Properties


class LibraryEntry:
    '''encapsulates all actions that can be taken for an individual game'''

    def __init__(self, parent_library, game: Game):
        self.parent_library = parent_library
        self.parent_window = parent_library.parent_window

        self.api = parent_library.api
        self.config = parent_library.config
        self.download_manager = parent_library.download_manager
        self.game = game

        self.offline = parent_library.offline
        self.thumbnail_set = False
        self.download_list = []
        self.dlc_dict = {}
        self.current_state = State.DOWNLOADABLE

        # Set folder for download installer
        self.download_dir = os.path.join(DOWNLOAD_DIR, self.game.get_install_directory_name())

        # Set folder if user wants to keep installer (disabled by default)
        self.keep_dir = os.path.join(self.config.install_dir, "installer")
        self.keep_path = os.path.join(self.keep_dir, self.game.get_install_directory_name())
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, mode=0o755)

    def init_ui_elements(self):
        self.image.set_tooltip_text(self.game.name)
        self.reload_state()
        load_thumbnail_thread = threading.Thread(target=self.load_thumbnail)
        load_thumbnail_thread.start()

        # Icon for Windows games
        if self.game.platform == "windows":
            self.image.set_tooltip_text("{} (Wine)".format(self.game.name))
            self.wine_icon.set_from_file(ICON_WINE_PATH)
            self.wine_icon.show()

    # Do not restart the download if Minigalaxy is restarted
    def prevent_resume_on_startup(self):
        self.config.remove_ongoing_download(self.game.id)

    def show_information(self, button):
        information_window = Information(self.parent_window, self.game, self.config, self.api, self.download_manager)
        information_window.run()
        information_window.destroy()

    def show_properties(self, button):
        properties_window = Properties(self.parent_library, self.game, self.config, self.api)
        properties_window.run()
        properties_window.destroy()

    def get_keep_executable_path(self):
        keep_path = ""
        if os.path.isdir(self.keep_path):
            for dir_content in os.listdir(self.keep_path):
                kept_file = os.path.join(self.keep_path, dir_content)
                if os.access(kept_file, os.X_OK) or os.path.splitext(kept_file)[-1] in [".exe", ".sh"]:
                    keep_path = kept_file
                    break
        return keep_path

    def get_download_info(self, platform="linux"):
        try:
            download_info = self.api.get_download_info(self.game, platform)
            result = True
        except NoDownloadLinkFound as e:
            logger.error("No download link found", exc_info=1)
            self.config.remove_ongoing_download(self.game.id)
            GLib.idle_add(self.parent_window.show_error, _("Download error"),
                          _("There was an error when trying to fetch the download link!\n{}".format(e)))
            download_info = False
            result = False
        return result, download_info

    def get_async_image_dlc_icon(self, dlc_id, image, icon, title):
        dlc_icon_path = os.path.join(ICON_DIR, "{}.jpg".format(dlc_id))
        if icon:
            if os.path.isfile(dlc_icon_path):
                GLib.idle_add(image.set_from_file, dlc_icon_path)
            else:
                url = "http:{}".format(icon)
                dlc_icon = os.path.join(ICON_DIR, "{}.jpg".format(dlc_id))
                download = Download(url, dlc_icon)
                self.download_manager.download_now(download)
                GLib.idle_add(image.set_from_file, dlc_icon_path)

    def set_progress(self, percentage: int):
        if self.current_state in [State.QUEUED, State.INSTALLED]:
            GLib.idle_add(self.update_to_state, State.DOWNLOADING)
        if self.progress_bar:
            GLib.idle_add(self.progress_bar.set_fraction, percentage / 100)
            GLib.idle_add(self.progress_bar.set_tooltip_text, "{}%".format(percentage))
