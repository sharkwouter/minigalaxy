import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
from minigalaxy.login import Login
from minigalaxy.window.gametile import GameTile
from minigalaxy.window.preferences import Preferences
from minigalaxy.api import Api
from minigalaxy.config import Config


@Gtk.Template.from_file("data/ui/application.ui")
class Window(Gtk.ApplicationWindow):

    __gtype_name__ = "Window"

    header_sync = Gtk.Template.Child()
    header_installed = Gtk.Template.Child()
    menu_about = Gtk.Template.Child()
    menu_preferences = Gtk.Template.Child()
    menu_logout = Gtk.Template.Child()
    library = Gtk.Template.Child()

    api = None

    tiles = []

    refresh_token_file = "refresh.txt"

    def __init__(self, name):
        Gtk.ApplicationWindow.__init__(self, title=name)
        self.config = Config()
        self.api = Api(self.config)
        self.show_installed_only = False

        self.__authenticate()

        self.show_all()

        self.sync_library(None)

    @Gtk.Template.Callback("on_header_sync_clicked")
    def sync_library(self, button):
        # Remove old game tiles
        for gametile in self.library.get_children():
            self.library.remove(gametile)

        # Get and add new ones
        games = self.api.get_library()
        tiles = []
        for game in games:
            gametile = GameTile(game=game, api=self.api)
            if not self.show_installed_only or gametile.installed:
                tiles.append(gametile)

        tiles.sort()
        for tile in tiles:
            self.library.add(tile)
        self.show_all()

    @Gtk.Template.Callback("on_header_installed_state_set")
    def show_installed_only_triggered(self, switch, state):
        self.show_installed_only = state
        self.sync_library(None)

    @Gtk.Template.Callback("on_menu_preferences_clicked")
    def show_preferences(self, button):
        preferences_window = Preferences(self.config)
        preferences_window.show()

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
