import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gui.mainwindow import MainWindow
from api.gog import GOGAPI

gog = GOGAPI()
#url = "https://embed.gog.com/on_login_success?origin=client&code=Khnp756_81Vra1WAjU3VMcOSI_T4af3VROLQ7Q-NkGkXSJ1XhlUQyPdZq_m06n6WPTT-GKNBwdY6vNFrPd-c1uFICzeOgOxl4LS4TLD3JbMC4dHlwVtfA5J3yIDNItV1o1sfnoJK0RI0UuYZUMTydgYoOeONyqX7Y-8ke2D3uVk"
#gog.authenticate(url)
window = MainWindow("python-gog-client", gog)
window.connect("destroy", Gtk.main_quit)
Gtk.main()