import os
import gi
from typing import List
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from minigalaxy.paths import UI_DIR
from minigalaxy.api import Api
from minigalaxy.game import Game


@Gtk.Template.from_file(os.path.join(UI_DIR, "library.ui"))
class Library(Gtk.Viewport):
    __gtype_name__ = "Library"

    flowbox = Gtk.Template.Child()

    def __init__(self, api: Api):
        Gtk.Viewport.__init__(self)
        self.games = []
        self.api = api

    def update_library(self) -> None:
        pass

    def __create_gametiles(self) -> None:
        pass

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
                file.close()
        return games

