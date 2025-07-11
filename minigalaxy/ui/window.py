import os
import locale

from minigalaxy.download_manager import DownloadManager
from minigalaxy.logger import logger
from minigalaxy.ui.categoryfilters import CategoryFilters
from minigalaxy.ui.login import Login
from minigalaxy.ui.preferences import Preferences
from minigalaxy.ui.about import About
from minigalaxy.api import Api
from minigalaxy.paths import UI_DIR, LOGO_IMAGE_PATH, THUMBNAIL_DIR, COVER_DIR, ICON_DIR
from minigalaxy.translation import _
from minigalaxy.ui.library import Library
from minigalaxy.ui.gtk import Gtk, Gdk, GdkPixbuf, Notify
from minigalaxy.config import Config
from minigalaxy.ui.download_list import DownloadManagerList


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
    download_list_button = Gtk.Template.Child()
    download_list = Gtk.Template.Child()

    def __init__(self, config: Config, api: 'Api', download_manager: DownloadManager, name="Minigalaxy"):
        current_locale = config.locale
        default_locale = locale.getdefaultlocale()[0]
        if current_locale == '':
            locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        else:
            try:
                locale.setlocale(locale.LC_ALL, (current_locale, 'UTF-8'))
            except NameError:
                locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
        Gtk.ApplicationWindow.__init__(self, title=name)

        self.api = api
        self.config = config
        self.download_manager = download_manager
        self.search_string = ""
        self.offline = False

        # Initialize notifications module
        Notify.init("minigalaxy")

        # Set library
        self.library = Library(self, config, api, download_manager)

        self.window_library.add(self.library)
        self.header_installed.set_active(self.config.installed_filter)
        self.download_list.add(DownloadManagerList(self.download_manager, self, self.config))

        # Set the icon
        icon = GdkPixbuf.Pixbuf.new_from_file(LOGO_IMAGE_PATH)
        self.set_default_icon_list([icon])

        # Set theme
        settings = Gtk.Settings.get_default()
        if self.config.use_dark_theme is True:
            settings.set_property("gtk-application-prefer-dark-theme", True)
        else:
            settings.set_property("gtk-application-prefer-dark-theme", False)

        # Show the window
        if self.config.keep_window_maximized:
            self.maximize()
        self.show_all()

        self.make_directories()

    def load_library(self):
        """
        This method attempts to connect to GOG and load all games. Must be called after initial construction of the window.
        It is separate from the constructor because this method might close the application on login errors.
        Before this happens, a destroy event for global resources like ThreadPools must be registered.
        Otherwise, the application will freeze.
        """
        # Interact with the API
        logger.debug("Checking API connectivity...")
        self.offline = not self.api.can_connect()
        logger.debug("Done checking API connectivity, status: %s", "offline" if self.offline else "online")
        if not self.offline:
            try:
                logger.debug("Authenticating...")
                self.__authenticate()
                logger.debug("Authenticated as: %s", self.api.get_user_info())
                self.HeaderBar.set_subtitle(self.api.get_user_info())
            except Exception:
                logger.warning("Starting in offline mode after receiving exception", exc_info=1)
                self.offline = True
        self.sync_library()

    @Gtk.Template.Callback("filter_library")
    def filter_library(self, switch, _=""):
        self.library.filter_library(switch)
        if switch == self.header_installed:
            self.config.installed_filter = switch.get_active()

    @Gtk.Template.Callback("on_menu_preferences_clicked")
    def show_preferences(self, button):
        preferences_window = Preferences(parent=self, config=self.config, download_manager=self.download_manager)
        preferences_window.run()
        preferences_window.destroy()

    @Gtk.Template.Callback("on_menu_about_clicked")
    def show_about(self, button):
        about_window = About(self)
        about_window.run()
        about_window.destroy()

    @Gtk.Template.Callback("on_menu_category_filter_clicked")
    def show_categories(self, button):
        category_filters_window = CategoryFilters(self, self.library)
        category_filters_window.run()
        category_filters_window.destroy()

    @Gtk.Template.Callback("on_menu_logout_clicked")
    def logout(self, button):
        question = _("Are you sure you want to log out of GOG?")
        if self.show_question(question):
            # Unset everything which is specific to this user
            self.HeaderBar.set_subtitle("")
            self.config.username = ""
            self.config.refresh_token = ""
            self.hide()
            # Show the login screen
            self.__authenticate()
            self.HeaderBar.set_subtitle(self.api.get_user_info())
            self.sync_library()
            self.show_all()

    @Gtk.Template.Callback("on_window_state_event")
    def on_window_state_event(self, widget, event):
        if event.new_window_state & Gdk.WindowState.MAXIMIZED:
            self.config.keep_window_maximized = True
        else:
            self.config.keep_window_maximized = False

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
        if self.config.stay_logged_in:
            token = self.config.refresh_token
        else:
            self.config.username = ""
            self.config.refresh_token = ""
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
                self.destroy()
                exit(0)
            if response == Gtk.ResponseType.NONE:
                result = login.get_result()
                authenticated = self.api.authenticate(login_code=result)

        self.config.refresh_token = authenticated
