import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from minigalaxy.login import Login
from minigalaxy.window.gametile import GameTile
from minigalaxy.window.preferences import Preferences
from minigalaxy.window.about import About
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.directories import UI_DIR


@Gtk.Template.from_file(os.path.join(UI_DIR, "application.ui"))
class Window(Gtk.ApplicationWindow):

    __gtype_name__ = "Window"

    header_sync = Gtk.Template.Child()
    header_installed = Gtk.Template.Child()
    header_search = Gtk.Template.Child()
    menu_about = Gtk.Template.Child()
    menu_preferences = Gtk.Template.Child()
    menu_logout = Gtk.Template.Child()
    library = Gtk.Template.Child()

    def __init__(self, name):
        Gtk.ApplicationWindow.__init__(self, title=name)
        self.config = Config()
        self.api = Api(self.config)
        self.show_installed_only = False
        self.search_string = ""
        self.tiles = []

        self.__authenticate()

        self.show_all()

        self.sync_library()

    @Gtk.Template.Callback("on_header_sync_clicked")
    def sync_library(self, button=None):
        # Remove old tiles
        for gametile in self.library.get_children():
            self.library.remove(gametile)

        # Get and add new ones
        games = self.api.get_library()
        self.tiles = []
        for game in games:
            gametile = GameTile(game=game, api=self.api)
            self.tiles.append(gametile)

        self.tiles.sort()
        for tile in self.tiles:
            self.library.add(tile)
            tile.show()

    @Gtk.Template.Callback("on_header_installed_state_set")
    def show_installed_only_triggered(self, switch, state):
        self.show_installed_only = state
        self.library.set_filter_func(self.filter_tiles)

    @Gtk.Template.Callback("on_header_search_changed")
    def search(self, widget):
        self.search_string = widget.get_text()
        self.library.set_filter_func(self.filter_tiles)

    @Gtk.Template.Callback("on_menu_preferences_clicked")
    def show_preferences(self, button):
        preferences_window = Preferences(self, self.config)
        preferences_window.show()

    @Gtk.Template.Callback("on_menu_about_clicked")
    def show_about(self, button):
        about_window = About(self)
        about_window.show()

    def filter_tiles(self, child):
        tile = child.get_children()[0]
        if tile.installed and self.show_installed_only or not self.show_installed_only:
            if self.search_string.lower() in str(tile).lower():
                return True
            else:
                return False
        else:
            return False

    """
    The API remembers the authentication token and uses it
    The token is not valid for a long time
    """
    def __authenticate(self):
        url = None
        token = self.config.get("refresh_token")

        authenticated = self.api.authenticate(refresh_token=token, login_code=url)

        while not authenticated:
            login_url = self.api.get_login_url()
            redirect_url = self.api.get_redirect_url()
            login = Login(login_url=login_url, redirect_url=redirect_url, parent=self)
            response = login.run()
            login.hide()
            if response == Gtk.ResponseType.NONE:
                print("This was your action")
                result = login.get_result()
                authenticated = self.api.authenticate(refresh_token=token, login_code=result)

        self.config.set("refresh_token", authenticated)
