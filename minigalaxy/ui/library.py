import json
import locale
import os
import re
import threading

from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.download_manager import DownloadManager
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.logger import logger
from minigalaxy.paths import UI_DIR, CATEGORIES_FILE_PATH
from minigalaxy.translation import _
from minigalaxy.ui.categoryfilters import CategoryFilters
from minigalaxy.ui.gametile import GameTile
from minigalaxy.ui.gametilelist import GameTileList
from minigalaxy.ui.gtk import Gtk, GLib

from typing import List


@Gtk.Template.from_file(os.path.join(UI_DIR, "library.ui"))
class Library(Gtk.Viewport):
    __gtype_name__ = "Library"

    flowbox = Gtk.Template.Child()

    def __init__(self, parent_window, config: Config, api: Api, download_manager: DownloadManager):
        Gtk.Viewport.__init__(self)

        self.parent_window = parent_window
        self.config = config

        current_locale = self.config.locale
        default_locale = locale.getdefaultlocale()[0]
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
        library_update_thread = threading.Thread(target=self.__update_library)
        library_update_thread.daemon = True
        library_update_thread.start()

    def __update_library(self):
        GLib.idle_add(self.__load_tile_states)
        self.owned_products_ids = self.api.get_owned_products_ids()
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

        if not self.config.show_hidden_games and tile.game.get_info("hide_game"):
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

    def __create_gametiles(self) -> None:
        """Gets called twice: Once for installed, once for not installed games."""
        games_with_tiles = []
        for child in self.flowbox.get_children():
            tile = child.get_children()[0]
            if tile.game in self.games:
                games_with_tiles.append(tile.game)
                """Games which already have a tile during the second invocation are installed games.
                These did NOT have api information about the thumbnail url in their Game instance in the first pass.
                Thus, they weren't able to load the thumbnail if it wasn't cached before. Try again now.
                This mostly applies when the user empties the cache. Otherwise THUMBNAIL dir should contain a file from
                when the game still wasn't installed
                """
                tile.load_thumbnail()

        for game in self.games:
            if game not in games_with_tiles:
                self.__add_gametile(game)

    def __add_gametile(self, game):
        view = self.config.view
        if view == "grid":
            game_tile = GameTile(self, game)
        elif view == "list":
            game_tile = GameTileList(self, game)

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
        return games

    def __add_games_from_api(self):
        retrieved_games, err_msg = self.api.get_library()
        if not err_msg:
            self.offline = False
        else:
            self.offline = True
            logger.info("Client is offline, showing installed games only")
            GLib.idle_add(self.parent_window.show_error, _("Failed to retrieve library"), _(err_msg))
        game_category_dict = {}
        for game in retrieved_games:
            if game not in self.games:
                self.games.append(game)

            local_game = self.games[self.games.index(game)]
            if local_game.id == 0 or local_game.name != game.name:
                local_game.id = game.id
                local_game.name = game.name

            local_game.image_url = game.image_url
            local_game.url = game.url
            local_game.category = game.category
            if len(game.category) > 0:  # exclude games without set category
                game_category_dict[game.name] = game.category
        update_game_categories_file(game_category_dict, CATEGORIES_FILE_PATH)


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
