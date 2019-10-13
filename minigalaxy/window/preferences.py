import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


@Gtk.Template.from_file("data/ui/preferences.ui")
class Preferences(Gtk.Dialog):
    __gtype_name__ = "Preferences"

    button_cancel = Gtk.Template.Child()
    button_save = Gtk.Template.Child()
    combobox_language = Gtk.Template.Child()
    entry_installpath = Gtk.Template.Child()

    def __init__(self):
        Gtk.Dialog.__init__(self, title="Preferences")
        languages = Gtk.ListStore(str, str)

        languages.append(["en", "English"])
        languages.append(["de", "German"])
        languages.append(["fr", "French"])
        languages.append(["es", "Spanish"])
        languages.append(["it", "Italian"])
        languages.append(["br", "Brazilian Portuguese"])
        languages.append(["pt", "Portuguese"])
        languages.append(["ru", "Russian"])
        languages.append(["pl", "Polish"])
        languages.append(["jp", "Japanese"])
        languages.append(["nl", "Dutch"])
        languages.append(["cn", "Chinese"])
        languages.append(["ko", "Korean"])
        languages.append(["tr", "Turkish"])
        languages.append(["hu", "Hungarian"])
        languages.append(["sv", "Swedish"])
        languages.append(["fi", "Finnish"])
        languages.append(["no", "Norwegian"])
        languages.append(["da", "Danish"])

        self.combobox_language.set_model(languages)
        self.combobox_language.set_entry_text_column(1)
        self.renderer_text = Gtk.CellRendererText()
        self.combobox_language.pack_start(self.renderer_text, False)

        self.show_all()

    @Gtk.Template.Callback("on_button_save_clicked")
    def save_pressed(self, button):
        self.response(Gtk.ResponseType.OK)
        self.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
