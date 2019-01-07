import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
from minigalaxy.login import Login
from minigalaxy.gametile import GameTile

@Gtk.Template.from_file("data/ui/application.ui")
class Window(Gtk.ApplicationWindow):

    __gtype_name__ = "Window"

    header_sync = Gtk.Template.Child()
    menu_about = Gtk.Template.Child()
    menu_preferences = Gtk.Template.Child()
    menu_logout = Gtk.Template.Child()
    library = Gtk.Template.Child()

    api = None

    refresh_token_file = "refresh.txt"

    def __init__(self, name, api):
        Gtk.ApplicationWindow.__init__(self, title=name)
        self.api = api

        self.__authenticate()

        self.show_all()

        self.sync_library(None)

    @Gtk.Template.Callback("on_header_sync_clicked")
    def sync_library(self, button):
        print("go get the library")
        games = self.api.get_library()
        for product in games['products']:
            print(product)
            gametile = GameTile(id=product["id"],name=product["title"], image=product["image"], api=self.api)
            self.library.add(gametile)
        self.show_all()

    """
    The API remembers the authentication token and uses it
    The token is not valid for a long time
    """
    def __authenticate(self):
        url = None
        token = None

        if os.path.isfile(self.refresh_token_file):
            with open("refresh.txt", 'r') as out:
                token = out.read()

        authenticated = self.api.authenticate(token=token, url=url)

        while not authenticated:
            login_url = self.api.get_login_url()
            redirect_url = self.api.get_redirect_url()
            login = Login(login_url=login_url, redirect_url=redirect_url, parent=self)
            response = login.run()
            login.hide()
            if response == Gtk.ResponseType.NONE:
                print("This was your action")
                result = login.get_result()
                authenticated = self.api.authenticate(token=token, url=result)

        with open("refresh.txt", 'w') as out:
            out.write(authenticated)
            out.close()
