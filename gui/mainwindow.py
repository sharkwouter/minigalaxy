import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from sys import platform
if not platform.startswith('darwin'):
    from gui.loginwindow import LoginWindow


@Gtk.Template.from_file("gui/glade/application.glade")
class MainWindow(Gtk.ApplicationWindow):

    __gtype_name__ = "Window"

    header_sync = Gtk.Template.Child()
    menu_about = Gtk.Template.Child()
    menu_preferences = Gtk.Template.Child()
    menu_logout = Gtk.Template.Child()
    library = Gtk.Template.Child()

    api = None

    def __init__(self, name, api):
        Gtk.ApplicationWindow.__init__(self, title=name)
        self.api = api
        self.api.read_refresh_token()
        self.api.refresh()
        self.show_all()

    @Gtk.Template.Callback("on_header_sync_clicked")
    def sync_library(self, button):
        print("go get the library")
        self.api.read_activate_token()
        games = self.api.get_library()
        for product in games['products']:
            print(product)
            button = Gtk.Button.new_with_label(product['title'])
            self.library.add(button)
        self.show_all()
