import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2
from gi.repository import Gtk

@Gtk.Template.from_file("data/ui/login.ui")
class Login(Gtk.Dialog):
    __gtype_name__ = "Login"

    box = Gtk.Template.Child()

    redirect_url = None

    result = None

    def __init__(self, login_url=None, redirect_url=None, parent=None):
        Gtk.Dialog.__init__(self, title="Login", parent=parent, flags=0, buttons=())

        self.redirect_url = redirect_url

        context = WebKit2.WebContext.new()
        webview = WebKit2.WebView.new_with_context(context)
        webview.load_uri(login_url)
        webview.connect('load-changed', self.on_navigation)

        self.box.pack_start(webview, True, True, 0)
        self.show_all()

    def on_navigation(self, widget, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = widget.get_uri()
            if uri.startswith(self.redirect_url):
                self.result = uri
                self.hide()

    def get_result(self):
        return self.result
