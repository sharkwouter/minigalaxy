import copy
import os
import gi
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from minigalaxy.paths import UI_DIR
from minigalaxy.api import Api
from minigalaxy.library import Library
from minigalaxy.ui.gamerow import GameRow

@Gtk.Template.from_file(os.path.join(UI_DIR, "list_library.ui"))
class ListLibrary(Gtk.Viewport):
    __gtype_name__ = "ListLibrary"

    listbox = Gtk.Template.Child()

    def __init__(self, parent, api: Api, show_installed_only = False, search_string = ""):
        Gtk.Viewport.__init__(self)
        self.parent = parent
        self.api = api
        self.show_installed_only = show_installed_only
        self.search_string = search_string
        self.offline = False
        self.library = Library(self.api)
        self.games = []

    def reset(self):
        self.games = []
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        self.listbox.show_all()
        self.update_library()

    def update_library(self) -> None:
        library_update_thread = threading.Thread(target=self.__update_library)
        library_update_thread.daemon = True
        library_update_thread.start()

    def __update_library(self):
        GLib.idle_add(self.__load_row_states)
        # Get games from library
        self.games = self.library.get_games()
        GLib.idle_add(self.__create_gamerow)
        GLib.idle_add(self.filter_library)

    def __load_row_states(self):
        for child in self.listbox.get_children():
            tile = child.get_children()[0]
            tile.reload_state()

    def filter_library(self, widget: Gtk.Widget = None):
        self.__load_row_states()
        if isinstance(widget, Gtk.Switch):
            self.show_installed_only = widget.get_active()
        elif isinstance(widget, Gtk.SearchEntry):
            self.search_string = widget.get_text()
        self.listbox.set_filter_func(self.__filter_library_func)

    def __filter_library_func(self, child):
        tile = child.get_children()[0]
        # Hide games which aren't installed while in offline mode
        installed=True if self.offline else self.show_installed_only
        return self.library.is_game_filtered(tile.game, installed=installed, name=self.search_string)

    def sort_library(self):
        self.listbox.set_sort_func(self.__sort_library_func)

    def __sort_library_func(self, child1, child2):
        tile1 = child1.get_children()[0].game
        tile2 = child2.get_children()[0].game
        return tile2 < tile1

    def __create_gamerow(self) -> None:
        games_with_rows = []
        games_with_removed_rows = []
        for child in self.listbox.get_children():
            row = child.get_children()[0]
            if row.current_state == row.state.INSTALLED:
                if not row.game.image_url:
                    games_with_removed_rows.append(copy.deepcopy(row.game))
                    self.listbox.remove(row)
                    continue
            if row.game in self.games:
                games_with_rows.append(row.game)

        for game in self.games:
            if game in games_with_rows:
                continue
            if game in games_with_removed_rows:
                for tile_game in games_with_removed_rows:
                    if game == tile_game:
                        game.install_dir = tile_game.install_dir
                        break
            self.__add_gamerow(game)

    def __add_gamerow(self, game):
        self.listbox.add(GameRow(self, game, self.api))
        self.sort_library()
        self.listbox.show_all()

    def __show_error(self, text, subtext):
        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.ERROR,
            parent=self.parent,
            modal=True,
            buttons=Gtk.ButtonsType.CLOSE,
            text=text
        )
        dialog.format_secondary_text(subtext)
        dialog.run()
        dialog.destroy()
