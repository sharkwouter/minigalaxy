import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from minigalaxy.ui.login import Login
from minigalaxy.ui.preferences import Preferences
from minigalaxy.ui.about import About
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.paths import UI_DIR, LOGO_IMAGE_PATH, THUMBNAIL_DIR
from minigalaxy.ui.library import Library


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
    window_library = Gtk.Template.Child()

    def __init__(self, name):
        Gtk.ApplicationWindow.__init__(self, title=name)
        self.config = Config()
        self.api = Api(self.config)
        self.show_installed_only = False
        self.search_string = ""
        self.offline = False

        # Set library
        self.library = Library(self, self.api, self.config)
        self.window_library.add(self.library)

        # Set the icon
        icon = GdkPixbuf.Pixbuf.new_from_file(LOGO_IMAGE_PATH)
        self.set_default_icon_list([icon])

        # Show the window
        self.show_all()

        # Create the thumbnails directory
        if not os.path.exists(THUMBNAIL_DIR):
            os.makedirs(THUMBNAIL_DIR)

        # Interact with the API
        self.__authenticate()
        self.HeaderBar.set_subtitle(self.api.get_user_info())
        self.sync_library()

    @Gtk.Template.Callback("filter_library")
    def filter_library(self, switch, _=""):
        self.library.filter_library(switch)

    @Gtk.Template.Callback("on_menu_preferences_clicked")
    def show_preferences(self, button):
        preferences_window = Preferences(self, self.config)
        preferences_window.run()
        preferences_window.destroy()

    @Gtk.Template.Callback("on_menu_about_clicked")
    def show_about(self, button):
        about_window = About(self)
        about_window.run()
        about_window.destroy()

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

    @Gtk.Template.Callback("on_header_sync_clicked")
    def sync_library(self, _=""):
        if self.library.offline:
            self.__authenticate()
        self.library.update_library()

    def reset_library(self):
        self.library.reset()

    """
    The API remembers the authentication token and uses it
    The token is not valid for a long time
    """
    def __authenticate(self):
        url = None
        if self.api.config.get("stay_logged_in"):
            token = self.config.get("refresh_token")
        else:
            self.config.unset("username")
            self.config.unset("refresh_token")
            token = None

        # Make sure there is an internet connection
        if not self.api.can_connect():
            return

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
