import os
from urllib.parse import urlparse, parse_qsl
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2
from gi.repository import Gtk
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR


@Gtk.Template.from_file(os.path.join(UI_DIR, "login.ui"))
class Login(Gtk.Dialog):
    __gtype_name__ = "Login"

    box = Gtk.Template.Child()

    redirect_url = None

    result = None

    def __init__(self, login_url=None, redirect_url=None, parent=None):
        Gtk.Dialog.__init__(self, title=_("Login"), parent=parent, flags=0, buttons=())

        self.redirect_url = redirect_url

        context = WebKit2.WebContext.new()
        webview = WebKit2.WebView.new_with_context(context)
        webview.load_uri(login_url)
        webview.connect('load-changed', self.on_navigation)

        self.box.pack_start(webview, True, True, 0)
        self.show_all()

    # Check if the login has completed when the page is changed. Set the result to the code value found within the url
    def on_navigation(self, widget, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = widget.get_uri()
            if uri.startswith(self.redirect_url):
                self.result = self.__get_code_from_url(uri)
                self.hide()

    # Return the code when can be used by the API to authenticate
    def get_result(self):
        return self.result

    # Get the code from the url returned by GOG when logging in has succeeded
    def __get_code_from_url(self, url: str):
        parsed_url = urlparse(url)
        input_params = dict(parse_qsl(parsed_url.query))
        return input_params.get('code')
