import os
import gi
import threading
from typing import List
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from minigalaxy.paths import UI_DIR
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.game import Game
from minigalaxy.ui.gametile import GameTile


@Gtk.Template.from_file(os.path.join(UI_DIR, "library.ui"))
class Library(Gtk.Viewport):
    __gtype_name__ = "Library"

    flowbox = Gtk.Template.Child()

    def __init__(self, parent, api: Api, config: Config):
        Gtk.Viewport.__init__(self)
        self.parent = parent
        self.api = api
        self.config = config
        self.show_installed_only = False
        self.search_string = ""
        self.games = []

    def reset(self):
        self.games = []
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)
        self.flowbox.show_all()
        self.update_library()

    def update_library(self) -> None:
        library_update_thread = threading.Thread(target=self.__update_library)
        library_update_thread.daemon = True
        library_update_thread.start()

    def __update_library(self):
        GLib.idle_add(self.__load_tile_states)
        # Get already installed games first
        self.games = self.__get_installed_games()
        self.__create_gametiles()

        # Get games from the API
        self.__add_games_from_api()
        self.__create_gametiles()

    def __load_tile_states(self):
        for child in self.flowbox.get_children():
            tile = child.get_children()[0]
            tile.load_state()

    def filter_library(self, widget: Gtk.Widget = None):
        if isinstance(widget, Gtk.Switch):
            self.show_installed_only = widget.get_active()
        elif isinstance(widget, Gtk.SearchEntry):
            self.search_string = widget.get_text()
        self.flowbox.set_filter_func(self.__filter_library_func)

    def __filter_library_func(self, child):
        tile = child.get_children()[0]
        if tile.game.install_dir and self.show_installed_only or not self.show_installed_only:
            if self.search_string.lower() in str(tile).lower():
                return True
        return False

    def sort_library(self):
        self.flowbox.set_sort_func(self.__sort_library_func)

    def __sort_library_func(self, child1, child2):
        tile1 = child1.get_children()[0].game
        tile2 = child2.get_children()[0].game
        return tile2 < tile1

    def __create_gametiles(self) -> None:
        games_with_tiles = []
        for child in self.flowbox.get_children():
            tile = child.get_children()[0]
            games_with_tiles.append(tile.game)

        for game in self.games:
            if game in games_with_tiles:
                continue
            GLib.idle_add(self.__add_gametile, game)

    def __add_gametile(self, game):
        self.flowbox.add(GameTile(self, game, self.api))
        self.sort_library()
        self.flowbox.show_all()

    def __get_installed_games(self) -> List[Game]:
        games = []
        directories = os.listdir(self.config.get("install_dir"))
        for directory in directories:
            full_path = os.path.join(self.config.get("install_dir"), directory)
            # Only scan directories
            if not os.path.isdir(full_path):
                continue
            # Make sure the gameinfo file exists
            gameinfo = os.path.join(full_path, "gameinfo")
            if not os.path.isfile(gameinfo):
                continue
            with open(gameinfo, 'r') as file:
                name = file.readline()
                games.append(Game(name=name.strip(), install_dir=full_path))
        return games

    def __add_games_from_api(self):
        try:
            retreived_games = self.api.get_library()
        except:
            return
        for game in retreived_games:
            if game not in self.games:
                self.games.append(game)
            else:
                # Make sure the game id is set if the game is installed
                for installed_game in self.games:
                    if game == installed_game:
                        if not installed_game.id:
                            installed_game.id = game.id
                        break
