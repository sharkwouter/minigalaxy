from urllib.parse import urlparse, parse_qsl
from minigalaxy.translation import _
from minigalaxy.ui.cert_dialog import CertDialog
from minigalaxy.ui.gtk import Gtk, load_ui
from minigalaxy.ui.webkit import WebKit2


@Gtk.Template(string=load_ui("login.ui"))
class BrowserWindow(Gtk.Dialog):
    __gtype_name__ = "Login"

    box = Gtk.Template.Child()
    urlbar = Gtk.Template.Child()

    def __init__(self, title=None, initial_url=None, width=400, height=600, is_modal=False, parent=None, **kwargs):
        Gtk.Dialog.__init__(self, parent=parent, flags=0, buttons=(), **kwargs)

        self.urlbar.connect('icon-press', self.on_certificate_icon_clicked)

        if parent and hasattr(parent, "webview"):
            self.webview = WebKit2.WebView.new_with_related_view(parent.webview)
        else:
            # https://stackoverflow.com/questions/9147875/webview-dont-display-javascript-windows-open
            settings = WebKit2.Settings.new()
            settings.props.javascript_can_open_windows_automatically = True
            self.webview = WebKit2.WebView.new_with_settings(settings)
        self.webview.load_uri(initial_url)
        self.webview.connect('load-changed', self.on_navigation)
        self.webview.connect('create', self.on_create)
        self.webview.connect('notify::title', self.on_title_change)
        self.webview.connect('close', self.on_close)

        if width and height:
            self.set_size_request(width, height)
        self.set_modal(is_modal)

        self.box.pack_start(self.webview, True, True, 0)

    # Create any pop-up windows during authentication
    def on_create(self, widget, action):
        popup = BrowserWindow(title=_("Login"),
                              initial_url=action.get_request().get_uri(),
                              width=400, height=600,
                              is_modal=True, parent=self)

        return popup.webview

    # When a pop up is closed (by Javascript), close the Gtk window too
    def on_close(self, widget):
        self.destroy()

    # Check if the login has completed when the page is changed. Set the result to the code value found within the url
    def on_navigation(self, widget, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = widget.get_uri()
            self.urlbar.set_text(uri)

    def on_title_change(self, widget, *args, **kwargs):
        self.set_title(widget.get_title())

    def on_certificate_icon_clicked(self, *args, **kwargs):
        # lines = []
        cert = self.webview.get_tls_info()[1]

        dialog = CertDialog(parent=self, cert=cert)
        dialog.run()
        """
        valid_from = cert.get_not_valid_before()
        valid_from = valid_from.format_iso8601() if valid_from else '-'
        valid_to = cert.get_not_valid_after()
        valid_to = valid_to.format_iso8601() if valid_to else '-'

        lines.append(_('Issuer: {}').format(cert.get_issuer_name()))
        lines.append(_('Subject: {}').format(cert.get_subject_name()))
        lines.append(_('Valid:\n\tfrom {}\n\tto {}').format(valid_from, valid_to))
        lines.append('')
        lines.append(_('Raw certificate data:'))
        lines.append(f'<span font-family="mono" size="smaller">{cert.props.certificate_pem}</span>')

        message = '\n'.join(lines)
        dialog = Gtk.MessageDialog(title=_("Show certificate"), parent=self,
                                   flags=Gtk.DialogFlags.MODAL,
                                   buttons=Gtk.ButtonsType.OK)
        dialog.set_markup(message)
        for w in dialog.get_message_area().get_children():
            if isinstance(w, Gtk.Label):
                w.set_selectable(True)
        dialog.connect('response', lambda *args: dialog.destroy())
        dialog.run()
        print(message)
        """


class Login():

    def __init__(self, login_url=None, redirect_url=None, parent=None):
        self.browser = BrowserWindow(title=_("Login"), initial_url=login_url, parent=parent)
        self.browser.webview.connect('load-changed', self.on_navigation)
        self.redirect_url = redirect_url

    def run(self):
        self.browser.show_all()
        return self.browser.run()

    def hide(self):
        self.browser.hide()

    def destroy(self):
        self.browser.destroy()

    # Check if the login has completed when the page is changed. Set the result to the code value found within the url
    def on_navigation(self, widget, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = widget.get_uri()
            # self.urlbar.set_text(uri)
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
