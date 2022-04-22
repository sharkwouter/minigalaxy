import os
import locale

from minigalaxy.ui.login import Login
from minigalaxy.ui.preferences import Preferences
from minigalaxy.ui.about import About
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.paths import UI_DIR, LOGO_IMAGE_PATH, THUMBNAIL_DIR, COVER_DIR, ICON_DIR
from minigalaxy.translation import _
from minigalaxy.ui.library import Library
from minigalaxy.ui.gtk import Gtk, Gdk, GdkPixbuf


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
        current_locale = Config.get("locale")
        default_locale = locale.getdefaultlocale()[0]
        if current_locale == '':
            locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        else:
            try:
                locale.setlocale(locale.LC_ALL, (current_locale, 'UTF-8'))
            except NameError:
                locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        Gtk.ApplicationWindow.__init__(self, title=name)

        self.api = Api()
        self.search_string = ""
        self.offline = False

        # Set library
        self.library = Library(self, self.api)
        self.window_library.add(self.library)
        self.header_installed.set_active(Config.get("installed_filter"))

        # Set the icon
        icon = GdkPixbuf.Pixbuf.new_from_file(LOGO_IMAGE_PATH)
        self.set_default_icon_list([icon])

        # Set theme
        settings = Gtk.Settings.get_default()
        if Config.get("use_dark_theme") is True:
            settings.set_property("gtk-application-prefer-dark-theme", True)
        else:
            settings.set_property("gtk-application-prefer-dark-theme", False)

        # Show the window
        if Config.get("keep_window_maximized"):
            self.maximize()
        self.show_all()

        self.make_directories()

        # Interact with the API
        self.offline = not self.api.can_connect()
        if not self.offline:
            try:
                self.__authenticate()
                self.HeaderBar.set_subtitle(self.api.get_user_info())
            except Exception as e:
                print(e)
                self.offline = True
        self.sync_library()

    @Gtk.Template.Callback("filter_library")
    def filter_library(self, switch, _=""):
        self.library.filter_library(switch)
        if switch == self.header_installed:
            Config.set("installed_filter", switch.get_active())

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
        question = _("Are you sure you want to log out of GOG?")
        if self.show_question(question):
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

    @Gtk.Template.Callback("on_window_state_event")
    def on_window_state_event(self, widget, event):
        if event.new_window_state & Gdk.WindowState.MAXIMIZED:
            Config.set("keep_window_maximized", True)
        else:
            Config.set("keep_window_maximized", False)

    @Gtk.Template.Callback("on_header_sync_clicked")
    def sync_library(self, _=""):
        if self.library.offline:
            self.__authenticate()
        self.library.update_library()

    def make_directories(self):
        # Create the thumbnails directory
        if not os.path.exists(THUMBNAIL_DIR):
            os.makedirs(THUMBNAIL_DIR, mode=0o755)
        # Create the covers directory
        if not os.path.exists(COVER_DIR):
            os.makedirs(COVER_DIR, mode=0o755)
        # Create the icons directory
        if not os.path.exists(ICON_DIR):
            os.makedirs(ICON_DIR, mode=0o755)

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
        dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
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
                authenticated = self.api.authenticate(login_code=result)

        Config.set("refresh_token", authenticated)
