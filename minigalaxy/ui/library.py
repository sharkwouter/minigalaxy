import json
import locale
import logging
import os
import re
import threading

from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.download_manager import DownloadManager
from minigalaxy.entity.state import State
from minigalaxy.game import Game, InfoKey
from minigalaxy.paths import CATEGORIES_FILE_PATH
from minigalaxy.translation import _
from minigalaxy.ui.categoryfilters import CategoryFilters
from minigalaxy.ui.gametile import GameTile
from minigalaxy.ui.gametilelist import GameTileList
from minigalaxy.ui.gtk import Gtk, GLib, load_ui

from typing import List


@Gtk.Template(string=load_ui("library.ui"))
class Library(Gtk.Viewport):
    __gtype_name__ = "Library"

    flowbox = Gtk.Template.Child()

    def __init__(self, parent_window, config: Config, api: Api, download_manager: DownloadManager):
        Gtk.Viewport.__init__(self)

        self.parent_window = parent_window
        self.config = config

        current_locale = self.config.locale
        default_locale = locale.getlocale()[0]
        if current_locale == '':
            locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        else:
            try:
                locale.setlocale(locale.LC_ALL, (current_locale, 'UTF-8'))
            except NameError:
                locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))

        self.api = api
        self.download_manager = download_manager
        self.show_installed_only = self.config.installed_filter
        self.search_string = ""
        self.offline = False
        self.games = []
        self.owned_products_ids = []
        self._queue = []
        self.category_filters = []
        self._library_generation = 0
        self.configure_library_sort()

    def _debounce(self, thunk):
        if thunk not in self._queue:
            self._queue.append(thunk)
            GLib.idle_add(self._run_queue)

    def _run_queue(self):
        queue, self._queue = self._queue, []
        for thunk in queue:
            GLib.idle_add(thunk)

    def reset(self):
        self.games = []
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)
        self.flowbox.show_all()
        self.update_library()

    def update_library(self) -> None:
        self._library_generation += 1
        generation = self._library_generation
        library_update_thread = threading.Thread(target=self.__update_library, args=(generation,))
        library_update_thread.daemon = True
        library_update_thread.start()

    def __update_library(self, generation):
        GLib.idle_add(self.__load_tile_states)
        self.owned_products_ids = self.api.get_owned_products_ids()
        installed = self.__get_installed_games()
        # Show installed before the API round-trip. Worker does not touch self.games.
        GLib.idle_add(self.__apply_installed_games, installed, generation)
        retrieved_games, err_msg = self.__fetch_library_from_api()
        GLib.idle_add(self.__apply_api_games, retrieved_games, err_msg, generation)

    def __apply_installed_games(self, installed, generation):
        if generation != self._library_generation:
            return False
        self.games = sorted(installed)
        self.filter_library()
        self.__create_gametiles(self.games)
        return False

    def __apply_api_games(self, retrieved_games, err_msg, generation):
        if generation != self._library_generation:
            return False
        self.__merge_api_games(retrieved_games, err_msg)
        self.games = [game for game in self.games if self.__should_show_game(game)]
        self.games.sort()
        self.filter_library()
        self.__create_gametiles(self.games)
        return False

    def __should_show_game(self, game) -> bool:
        return (
            game.is_installed()
            or game.id in self.config.current_downloads
            or game.platform in self.config.platform_mode
        )

    def __load_tile_states(self):
        for child in self.flowbox.get_children():
            tile = child.get_children()[0]
            tile.reload_state()

    def filter_library(self, widget: Gtk.Widget = None):
        if isinstance(widget, Gtk.Switch):
            self.show_installed_only = widget.get_active()
        elif isinstance(widget, Gtk.SearchEntry):
            self.search_string = widget.get_text()
        elif isinstance(widget, Gtk.Dialog) and isinstance(widget, CategoryFilters):
            # filter all true category-bool pairs and then extract category names
            self.category_filters = [j[0] for j in filter(lambda i: i[1], widget.filter_dict.items())]
        self.flowbox.set_filter_func(self.__filter_library_func)

    def __filter_library_func(self, child):
        tile = child.get_children()[0]
        if self.search_string.lower() not in str(tile).lower():
            return False

        if self.show_installed_only:
            if tile.current_state in [State.DOWNLOADABLE, State.INSTALLABLE]:
                return False

        if not self.config.show_hidden_games and tile.game.get_info(InfoKey.HIDE_GAME):
            return False

        if len(self.category_filters) > 0:
            if tile.game.category not in self.category_filters:
                return False

        return True

    def configure_library_sort(self):
        self.flowbox.set_sort_func(self.__sort_library_func)

    def __sort_library_func(self, child1, child2):
        tile1 = child1.get_children()[0].game
        tile2 = child2.get_children()[0].game
        return tile2 < tile1

    def __create_gametiles(self, games_to_add=None) -> None:
        """Gets called twice: Once for installed, once for not installed games."""

        if not games_to_add:
            games_to_add = self.games

        logging.debug("Create gametiles for %s games", str(len(games_to_add)))

        for child in self.flowbox.get_children():
            tile = child.get_children()[0]
            if tile.game in games_to_add:
                logging.debug("Update existing tile for [%s] with new game instance", tile.game.name)
                new_game = games_to_add[games_to_add.index(tile.game)]
                new_game.library_tile = tile
                tile.game = new_game

        for game in games_to_add:
            if game.library_tile:
                # the game already has a visible entry in the library
                # request to load the thumbnail, if there is a url for it and it hasnt been loaded before
                game.library_tile.load_thumbnail()
                continue
            if self.__should_show_game(game):
                self.__add_gametile(game)

    def __add_gametile(self, game):
        view = self.config.view
        if view == "grid":
            game_tile = GameTile(self, game)
        elif view == "list":
            game_tile = GameTileList(self, game)
        game.library_tile = game_tile

        # Start download if Minigalaxy was closed while downloading this game
        game_tile.resume_download_if_expected()
        self.flowbox.add(game_tile)
        '''
        using flowbox.show_all at this point would overrule any state-based
        hide() statements in game_tile (progress_bar in GameTileList)
        '''
        game_tile.show()

    def __get_installed_games(self) -> List[Game]:
        # Make sure the install directory exists
        library_dir = self.config.install_dir
        if not os.path.exists(library_dir):
            os.makedirs(library_dir, mode=0o755)
        directories = os.listdir(library_dir)
        games = []
        game_categories_dict = read_game_categories_file(CATEGORIES_FILE_PATH)
        for directory in directories:
            full_path = os.path.join(self.config.install_dir, directory)
            # Only scan directories
            if not os.path.isdir(full_path):
                continue
            # Make sure the gameinfo file exists
            gameinfo = os.path.join(full_path, "gameinfo")
            if os.path.isfile(gameinfo):
                with open(gameinfo, 'r') as file:
                    name = file.readline().strip()
                    version = file.readline().strip()      # noqa: F841
                    version_dev = file.readline().strip()  # noqa: F841
                    language = file.readline().strip()     # noqa: F841
                    game_id = file.readline().strip()
                    if not game_id:
                        game_id = 0
                    else:
                        game_id = int(game_id)
                category = game_categories_dict.get(name, "")
                games.append(Game(name=name, game_id=game_id, install_dir=full_path, category=category))
            else:
                games.extend(get_installed_windows_games(full_path, game_categories_dict))

        # try to repair a corrupted list of ongoing downloads
        # if something is considered 'installed', it shouldn't be on the download list anymore
        self.config.start_batch_edit()
        for game in games:
            self.config.remove_ongoing_download(game.id)
        self.config.save()

        return games

    def __fetch_library_from_api(self):
        logging.info("Start retrieving owned games from the api...")
        return self.api.get_library()

    def __add_games_from_api(self):
        retrieved_games, err_msg = self.__fetch_library_from_api()
        self.__merge_api_games(retrieved_games, err_msg)

    def __merge_api_games(self, retrieved_games, err_msg):
        if not err_msg:
            self.offline = False
        else:
            self.offline = True
            logging.info("Client is offline, showing installed games only")
            GLib.idle_add(self.parent_window.show_error, _("Failed to retrieve library"), _(err_msg))
        game_category_dict = {}
        logging.info("Create or update the game list with %s games", len(retrieved_games))
        for game in retrieved_games:
            # NOTE: the 'in' check and 'list.index' function depend on the '__eq__' method of Game.
            # 'Game.__eq__(self, other)' is a bit lenient, it ignores the property 'id' if it is zero for 'self' or 'other'.
            # This leniency is vital in correctly detecting installed games with missing metadata.

            # add game to list which is not installed
            if game not in self.games:
                self.games.append(game)

            local_game = self.games[self.games.index(game)]
            # update the local Game instance with data retrieved from remote, but only when both are not the same instance
            _update_gameinfo(local_game, game, game_category_dict)

        update_game_categories_file(game_category_dict, CATEGORIES_FILE_PATH)


def _update_gameinfo(local_game, api_game, game_category_dict={}):
    """
    Installed games are detected first, and they will be missing some information provided by GOG.
    This function takes a local Game and a freshly obtained Game from API and updates the local instance with
    a select list of properties from API.
    'game_category_dict' is used for library filters and should be passed in from the caller.
    """

    if len(api_game.category) > 0:  # exclude games without set category
        game_category_dict[api_game.name] = api_game.category

    local_game.update_from_other(api_game)


def get_installed_windows_games(full_path, game_categories_dict=None):
    games = []
    game_files = os.listdir(full_path)
    for file in game_files:
        if re.match(r'^goggame-[0-9]*\.info$', file):
            with open(os.path.join(full_path, file), 'rb') as info_file:
                info = json.loads(info_file.read().decode('utf-8-sig'))
                if not info.get('playTasks', []):
                    continue

                game = Game(
                    name=info["name"],
                    game_id=int(info["gameId"]),
                    install_dir=full_path,
                    platform="windows",
                    category=(game_categories_dict or {}).get(info["name"], "")
                )
                games.append(game)
    return games


def update_game_categories_file(game_category_dict, categories_file_path):
    if len(game_category_dict) == 0:
        return
    if not os.path.exists(categories_file_path):  # if file does not exist, create it and write dict
        with open(categories_file_path, 'wt') as fd:
            json.dump(game_category_dict, fd)
    else:
        with open(categories_file_path, 'r+t') as fd:  # if file exists, write dict only if not equal to file data
            cached_game_category_dict = json.load(fd)
            if game_category_dict != cached_game_category_dict:
                fd.seek(os.SEEK_SET)
                fd.truncate(0)
                json.dump(game_category_dict, fd)


def read_game_categories_file(categories_file_path):
    cached_game_category_dict = {}
    if os.path.exists(categories_file_path):
        with open(categories_file_path, 'rt') as fd:
            cached_game_category_dict = json.load(fd)
    return cached_game_category_dict
