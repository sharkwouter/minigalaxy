import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gui.loginwindow import LoginWindow


class MainWindow(Gtk.Window):

    def __init__(self, name, api):
        self.api = api
        Gtk.Window.__init__(self, title=name)

        # Load the content of the window from a glade file

        builder = Gtk.Builder()
        builder.add_from_file("gui/glade/mainwindow.glade")
        builder.connect_signals(self)

        vbox = builder.get_object("vbox")

        self.library = builder.get_object("window_library")


        #self.button_box = Gtk.Box()


        #self.library_button = Gtk.Button.new_with_label("library")
        #self.library_button.connect("clicked", self.on_button_get_library_clicked)
        #self.button_box.pack_start(self.library_button, True, True, 0)

        self.add(vbox)
        self.show_all()

    def on_button_login_clicked(self, button):
        LoginWindow(self.api)

    def on_button_refresh_token_clicked(self, button):
        print("token needs to be refreshed")
        self.api.read_refresh_token()
        self.api.refresh()

    def on_button_get_library_clicked(self, button):
        print("go get the library")
        self.api.read_activate_token()
        games = self.api.get_library()
        game_number = 0
        for product in games['products']:
            game_number += 1
            print("{}: {}".format(game_number, product['title']))
            button = Gtk.Button.new_with_label(product['title'])
            self.library.add(button)
        self.show_all()

