from minigalaxy.ui.gtk import Gtk, load_ui
from minigalaxy.translation import _


@Gtk.Template(string=load_ui("cert_window.ui"))
class CertDialog(Gtk.Dialog):
    __gtype_name__ = "CertDialog"

    entry_issuer = Gtk.Template.Child()
    entry_subject = Gtk.Template.Child()
    entry_valid_from = Gtk.Template.Child()
    entry_valid_to = Gtk.Template.Child()
    text_cert_raw = Gtk.Template.Child()

    def __init__(self, parent=None, cert=None):
        Gtk.Dialog.__init__(self, title=_('Show certificate'), parent=parent)
        self.add_button(_('Close'), Gtk.ResponseType.CLOSE)

        valid_from = cert.get_not_valid_before()
        valid_from = valid_from.format_iso8601() if valid_from else '-'
        valid_to = cert.get_not_valid_after()
        valid_to = valid_to.format_iso8601() if valid_to else '-'

        self.entry_issuer.set_text(cert.get_issuer_name())
        self.entry_subject.set_text(cert.get_subject_name())
        self.entry_valid_from.set_text(valid_from)
        self.entry_valid_to.set_text(valid_to)

        buffer = self.text_cert_raw.get_buffer()
        buffer.set_text(cert.props.certificate_pem)
        self.connect('response', lambda *args: self.destroy())
