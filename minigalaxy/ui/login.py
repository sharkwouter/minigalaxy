import os
from urllib.parse import urlparse, parse_qsl
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.ui.gtk import Gtk
from minigalaxy.ui.webkit import WebKit2


@Gtk.Template.from_file(os.path.join(UI_DIR, "login.ui"))
class Login(Gtk.Dialog):
    __gtype_name__ = "Login"

    box = Gtk.Template.Child()

    redirect_url = None

    result = None

    def __init__(self, login_url=None, redirect_url=None, parent=None):
        Gtk.Dialog.__init__(self, title=_("Login"), parent=parent, flags=0, buttons=())

        self.redirect_url = redirect_url

        # https://stackoverflow.com/questions/9147875/webview-dont-display-javascript-windows-open
        settings = WebKit2.Settings.new()
        settings.props.javascript_can_open_windows_automatically = True
        webview = WebKit2.WebView.new_with_settings(settings)
        webview.load_uri(login_url)
        webview.connect('load-changed', self.on_navigation)
        webview.connect('create', self.on_create)

        self.box.pack_start(webview, True, True, 0)
        self.show_all()

    # Check if the login has completed when the page is changed. Set the result to the code value found within the url
    def on_navigation(self, widget, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = widget.get_uri()
            if uri.startswith(self.redirect_url):
                self.result = self.__get_code_from_url(uri)
                self.hide()

    # Create any pop-up windows during authentication
    def on_create(self, widget, action):
        popup = Gtk.Dialog(title=_("Facebook Login"), parent=self, flags=0, buttons=())
        webview = WebKit2.WebView.new_with_related_view(widget)
        webview.load_uri(action.get_request().get_uri())
        webview.__dict__['popup'] = popup
        webview.connect('close', self.on_close_popup)
        popup.get_content_area().pack_start(webview, True, True, 0)
        popup.set_size_request(400, 600)
        popup.set_modal(True)
        popup.show_all()
        return webview

    # When a pop up is closed (by Javascript), close the Gtk window too
    def on_close_popup(self, widget):
        if 'popup' in widget.__dict__:
            widget.__dict__['popup'].hide()

    # Return the code when can be used by the API to authenticate
    def get_result(self):
        return self.result

    # Get the code from the url returned by GOG when logging in has succeeded
    def __get_code_from_url(self, url: str):
        parsed_url = urlparse(url)
        input_params = dict(parse_qsl(parsed_url.query))
        return input_params.get('code')
