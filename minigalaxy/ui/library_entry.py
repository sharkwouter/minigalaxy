from minigalaxy.game import Game
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

    def show_information(self, button):
        information_window = Information(self.parent_window, self.game, self.config, self.api, self.download_manager)
        information_window.run()
        information_window.destroy()

    def show_properties(self, button):
        properties_window = Properties(self.parent_library, self.game, self.config, self.api)
        properties_window.run()
        properties_window.destroy()
