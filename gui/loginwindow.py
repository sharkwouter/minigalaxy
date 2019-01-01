import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2
from gi.repository import Gtk

class LoginWindow(Gtk.Window):

    def __init__(self, api, parent=None):
        self.api = api
        Gtk.Window.__init__(self, title=self.api.get_name(), parent=parent)

        self.set_border_width(0)
        self.set_default_size(390, 510)

        self.context = WebKit2.WebContext.new()
        self.webview = WebKit2.WebView.new_with_context(self.context)
        self.webview.load_uri(self.api.get_login_url())
        self.webview.connect('load-changed', self.on_navigation)

        self.add(self.webview)
        self.show_all()

    def on_navigation(self, widget, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = widget.get_uri()
            if uri.startswith(self.api.get_redirect_uri()):
                print("success: " + uri)
                self.api.authenticate(uri)
                self.destroy()
