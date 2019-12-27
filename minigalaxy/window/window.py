import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from minigalaxy.window.login import Login
from minigalaxy.window.gametile import GameTile
from minigalaxy.window.preferences import Preferences
from minigalaxy.window.about import About
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.paths import UI_DIR, LOGO_IMAGE_PATH, THUMBNAIL_DIR


@Gtk.Template.from_file(os.path.join(UI_DIR, "application.ui"))
class Window(Gtk.ApplicationWindow):

    __gtype_name__ = "Window"

    HeaderBar = Gtk.Template.Child()
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

        # Set the icon
        icon = GdkPixbuf.Pixbuf.new_from_file(LOGO_IMAGE_PATH)
        self.set_default_icon_list([icon])

        # Create the thumbnails directory
        if not os.path.exists(THUMBNAIL_DIR):
            os.makedirs(THUMBNAIL_DIR)

        # Interact with the API
        self.__authenticate()
        self.HeaderBar.set_subtitle(self.api.get_user_info())
        self.sync_library()

        self.show_all()

    @Gtk.Template.Callback("on_header_sync_clicked")
    def sync_library(self, button=None):
        # Get and add new games
        games = self.api.get_library()

        # Make a list with the game tiles which are already loaded
        current_tiles = []
        for child in self.library.get_children():
            tile = child.get_children()[0]
            current_tiles.append(tile)

        # Only add games if they aren't already in the list. Otherwise just reload their state
        for game in games:
            not_found = True
            for tile in current_tiles:
                if tile.game.id == game.id:
                    not_found = False
                    break
            if not_found:
                gametile = GameTile(parent=self, game=game, api=self.api)
                self.library.add(gametile)

        self.sort_library()
        self.filter_library()
        self.library.show_all()

    @Gtk.Template.Callback("on_header_installed_state_set")
    def show_installed_only_triggered(self, switch, state):
        self.show_installed_only = state
        self.library.set_filter_func(self.__filter_library_func)

    @Gtk.Template.Callback("on_header_search_changed")
    def search(self, widget):
        self.search_string = widget.get_text()
        self.library.set_filter_func(self.__filter_library_func)

    @Gtk.Template.Callback("on_menu_preferences_clicked")
    def show_preferences(self, button):
        preferences_window = Preferences(self, self.config)
        preferences_window.show()

    @Gtk.Template.Callback("on_menu_about_clicked")
    def show_about(self, button):
        about_window = About(self)
        about_window.show()

    @Gtk.Template.Callback("on_menu_logout_clicked")
    def logout(self, button):
        # Unset everything which is specific to this user
        self.HeaderBar.set_subtitle("")
        self.config.unset("username")
        self.config.unset("refresh_token")
        self.hide()

        # Show the login screen
        self.__authenticate()
        self.HeaderBar.set_subtitle(self.api.get_user_info())
        self.sync_library()

        self.show_all()

    def refresh_game_install_states(self):
        for child in self.library.get_children():
            tile = child.get_children()[0]
            tile.load_state()
        self.filter_library()

    def filter_library(self):
        self.library.set_filter_func(self.__filter_library_func)

    def __filter_library_func(self, child):
        tile = child.get_children()[0]
        if tile.installed and self.show_installed_only or not self.show_installed_only:
            if self.search_string.lower() in str(tile).lower():
                return True
            else:
                return False
        else:
            return False

    def sort_library(self):
        self.library.set_sort_func(self.__sort_library_func)

    def __sort_library_func(self, child1, child2):
        tile1 = child1.get_children()[0]
        tile2 = child2.get_children()[0]
        return tile2 < tile1

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
            if response == Gtk.ResponseType.DELETE_EVENT:
                Gtk.main_quit()
                exit(0)
            if response == Gtk.ResponseType.NONE:
                result = login.get_result()
                authenticated = self.api.authenticate(refresh_token=token, login_code=result)

        self.config.set("refresh_token", authenticated)
