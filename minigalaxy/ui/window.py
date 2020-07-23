import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from minigalaxy.ui.login import Login
from minigalaxy.ui.preferences import Preferences
from minigalaxy.ui.about import About
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.download_manager import DownloadManager
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

    def __init__(self, name="Minigalaxy"):
        Gtk.ApplicationWindow.__init__(self, title=name)
        self.api = Api()
        self.show_installed_only = False
        self.search_string = ""
        self.offline = False

        # Make the DownloadManager able to output errors
        DownloadManager.window = self

        # Set library
        self.library = Library(self, self.api)
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
        preferences_window = Preferences(self)
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
        Config.unset("username")
        Config.unset("refresh_token")
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

    def update_library(self):
        self.library.update_library()

    def show_error(self, text, secondary_text=""):
        dialog = Gtk.MessageDialog(
            parent=self,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=text
        )
        if secondary_text:
            dialog.format_secondary_text(secondary_text)
        dialog.run()
        dialog.destroy()

    def show_question(self, text, secondary_text=""):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            message_format=text
        )
        if secondary_text:
            dialog.format_secondary_text(secondary_text)
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.OK

    """
    The API remembers the authentication token and uses it
    The token is not valid for a long time
    """

    def __authenticate(self):
        url = None
        if Config.get("stay_logged_in"):
            token = Config.get("refresh_token")
        else:
            Config.unset("username")
            Config.unset("refresh_token")
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

        Config.set("refresh_token", authenticated)
