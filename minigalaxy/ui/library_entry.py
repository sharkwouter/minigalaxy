import os

from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.paths import CACHE_DIR, DOWNLOAD_DIR
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

    def show_information(self, button):
        information_window = Information(self.parent_window, self.game, self.config, self.api, self.download_manager)
        information_window.run()
        information_window.destroy()

    def show_properties(self, button):
        properties_window = Properties(self.parent_library, self.game, self.config, self.api)
        properties_window.run()
        properties_window.destroy()
