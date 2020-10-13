import copy
import os
import re
import json
import gi
import threading
from typing import List
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from minigalaxy.paths import UI_DIR
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.game import Game
from minigalaxy.ui.gametile import GameTile
from minigalaxy.translation import _


@Gtk.Template.from_file(os.path.join(UI_DIR, "library.ui"))
class Library(Gtk.Viewport):
    __gtype_name__ = "Library"

    flowbox = Gtk.Template.Child()

    def __init__(self, parent, api: Api):
        Gtk.Viewport.__init__(self)
        self.parent = parent
        self.api = api
        self.show_installed_only = False
        self.search_string = ""
        self.offline = False
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
        GLib.idle_add(self.__create_gametiles)

        # Get games from the API
        self.__add_games_from_api()
        GLib.idle_add(self.__create_gametiles)
        GLib.idle_add(self.filter_library)

    def __load_tile_states(self):
        for child in self.flowbox.get_children():
            tile = child.get_children()[0]
            tile.reload_state()

    def filter_library(self, widget: Gtk.Widget = None):
        self.__load_tile_states()
        if isinstance(widget, Gtk.Switch):
            self.show_installed_only = widget.get_active()
        elif isinstance(widget, Gtk.SearchEntry):
            self.search_string = widget.get_text()
        self.flowbox.set_filter_func(self.__filter_library_func)

    def __filter_library_func(self, child):
        tile = child.get_children()[0]
        # Hide games which aren't installed while in offline mode
        if not tile.game.install_dir and self.offline:
            return False
        if tile.current_state == tile.state.INSTALLED and self.show_installed_only or not self.show_installed_only:
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
        games_with_removed_tiles = []
        for child in self.flowbox.get_children():
            tile = child.get_children()[0]
            if tile.current_state == tile.state.INSTALLED:
                if not tile.game.image_url:
                    games_with_removed_tiles.append(copy.deepcopy(tile.game))
                    self.flowbox.remove(tile)
                    continue
            if tile.game in self.games:
                games_with_tiles.append(tile.game)

        for game in self.games:
            if game in games_with_tiles:
                continue
            if game in games_with_removed_tiles:
                for tile_game in games_with_removed_tiles:
                    if game == tile_game:
                        game.install_dir = tile_game.install_dir
                        break
            self.__add_gametile(game)

    def __add_gametile(self, game):
        self.flowbox.add(GameTile(self, game, self.api))
        self.sort_library()
        self.flowbox.show_all()

    def __get_installed_games(self) -> List[Game]:
        games = []
        directories = os.listdir(Config.get("install_dir"))
        for directory in directories:
            full_path = os.path.join(Config.get("install_dir"), directory)
            # Only scan directories
            if not os.path.isdir(full_path):
                continue
            # Make sure the gameinfo file exists
            gameinfo = os.path.join(full_path, "gameinfo")
            if os.path.isfile(gameinfo):
                with open(gameinfo, 'r') as file:
                    name = file.readline().strip()
                    version = file.readline().strip()
                    version_dev = file.readline().strip()
                    language = file.readline().strip()
                    game_id = file.readline().strip()
                    if not game_id:
                        game_id = 0
                    else:
                        game_id = int(game_id)
                games.append(Game(name=name, game_id=game_id, install_dir=full_path))
            else:
                game_files = os.listdir(full_path)
                for file in game_files:
                    if re.match(r'^goggame-[0-9]*\.info$', file):
                        with open(os.path.join(full_path, file), 'r') as info_file:
                            info = json.loads(info_file.read())
                            game = Game(
                                name=info["name"],
                                game_id=int(info["gameId"]),
                                install_dir=full_path,
                                platform="windows"
                            )
                            games.append(game)
        return games

    def __add_games_from_api(self):
        try:
            retrieved_games = self.api.get_library()
            self.offline = False
        except:
            self.offline = True
            GLib.idle_add(self.parent.show_error, _("Failed to retrieve library"), _("Couldn't connect to GOG servers"))
            return
        installed_game_names = []
        for game in self.games:
            installed_game_names.append(game.name.lower())
        for game in retrieved_games:
            if game.name.lower() not in installed_game_names:
                self.games.append(game)


