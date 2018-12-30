import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gui.loginwindow import LoginWindow
from api.gog import GOGAPI

gog = GOGAPI()
thing = LoginWindow(gog)
thing.connect("destroy", Gtk.main_quit)
Gtk.main()
print("test")
