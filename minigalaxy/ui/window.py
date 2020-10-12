import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from minigalaxy.ui.login import Login
from minigalaxy.ui.preferences import Preferences
from minigalaxy.ui.about import About
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.paths import UI_DIR, LOGO_IMAGE_PATH, THUMBNAIL_DIR
from minigalaxy.ui.grid_library import GridLibrary
from minigalaxy.ui.list_library import ListLibrary


@Gtk.Template.from_file(os.path.join(UI_DIR, "application.ui"))
class Window(Gtk.ApplicationWindow):
    __gtype_name__ = "Window"

    HeaderBar = Gtk.Template.Child()
    header_sync = Gtk.Template.Child()
    header_viewas = Gtk.Template.Child();
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
        self.library = None
        
        res = self.get_screen_resolution()
        # we got resolution
        if res[0] > 0 and res[0] <= 1368:
            self.set_default_size(1024,700)
        
        img = self.header_viewas.get_children()[0];
        iconsize = img.get_icon_name().size;
        
        # Set default state for the installed switch
        if (Config.get("filter_installed") == True):
            self.show_installed_only=True
            self.header_installed.set_state(True)

        # Set library view mode
        if (Config.get("viewas") == "list"):
            img.set_from_icon_name("view-grid-symbolic",iconsize)
            self.header_viewas.set_tooltip_text("View as Grid")
            self.library = ListLibrary(self, self.api, show_installed_only=self.show_installed_only)
        else:
            img.set_from_icon_name("view-list-symbolic",iconsize)
            self.header_viewas.set_tooltip_text("View as List")
            self.library = GridLibrary(self, self.api, show_installed_only=self.show_installed_only)
        
        self.window_library.add(self.library)

        # Set the icon
        icon = GdkPixbuf.Pixbuf.new_from_file(LOGO_IMAGE_PATH)
        self.set_default_icon_list([icon])

        # Show the window
        self.show_all()

        # Create the thumbnails directory
        if not os.path.exists(THUMBNAIL_DIR):
            os.makedirs(THUMBNAIL_DIR, mode=0o755)

        # Interact with the API
        self.__authenticate()
        self.HeaderBar.set_subtitle(self.api.get_user_info())
        self.sync_library()
        
    def get_screen_resolution(self, measurement="px"):
        """
        Tries to detect the screen resolution from the system.
        @param measurement: The measurement to describe the screen resolution in. Can be either 'px', 'inch' or 'mm'. 
        @return: (screen_width,screen_height) where screen_width and screen_height are int types according to measurement.
        """
        mm_per_inch = 25.4
        try: # Platforms supported by GTK3, Fx Linux/BSD
            screen = Gdk.Screen.get_default()
            if measurement=="px":
                width = screen.get_width()
                height = screen.get_height()
            elif measurement=="inch":
                width = screen.get_width_mm()/mm_per_inch
                height = screen.get_height_mm()/mm_per_inch
            elif measurement=="mm":
                width = screen.get_width_mm()
                height = screen.get_height_mm()
            else:
                raise NotImplementedError("Handling %s is not implemented." % measurement)
            return (width,height)
        except Exception as ex:
            print("Could not obtain screen resolution. Cause: {}".format(ex))
            return (-1,-1)

    @Gtk.Template.Callback("filter_library")
    def filter_library(self, switch, _=""):
        if (self.library is not None):
            Config.set("filter_installed", False if switch.get_state() else True)
            self.show_installed_only = False if switch.get_state() else True
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
        
    @Gtk.Template.Callback("on_header_viewas_clicked")
    def library_viewas(self, _=""):
        self.window_library.remove(self.library)
        self.library.destroy()
        img = self.header_viewas.get_children()[0];
        iconname = img.get_icon_name().icon_name;
        iconsize = img.get_icon_name().size;
        if (iconname == "view-list-symbolic"):
            img.set_from_icon_name("view-grid-symbolic",iconsize)
            Config.set("viewas","list")
            self.header_viewas.set_tooltip_text("View as Grid")
            self.library = ListLibrary(self, self.api, show_installed_only=self.show_installed_only, search_string=self.header_search.get_text())
        else:
            img.set_from_icon_name("view-list-symbolic",iconsize)
            Config.set("viewas","grid")
            self.header_viewas.set_tooltip_text("View as List")
            self.library = GridLibrary(self, self.api, show_installed_only=self.show_installed_only, search_string=self.header_search.get_text())
        self.window_library.add(self.library)
        self.sync_library()

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
        try:
            if not self.api.can_connect():
                return
        except Exception as ex:
            print("Encountered error while trying to check if an API connection is possible. Got error: {}".format(ex))
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
