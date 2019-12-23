import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
from minigalaxy.directories import UI_DIR

SUPPORTED_LANGUAGES = [
    ["br", "Brazilian Portuguese"],
    ["cn", "Chinese"],
    ["da", "Danish"],
    ["nl", "Dutch"],
    ["en", "English"],
    ["fi", "Finnish"],
    ["fr", "French"],
    ["de", "German"],
    ["hu", "Hungarian"],
    ["it", "Italian"],
    ["jp", "Japanese"],
    ["ko", "Korean"],
    ["no", "Norwegian"],
    ["pl", "Polish"],
    ["pt", "Portuguese"],
    ["ru", "Russian"],
    ["es", "Spanish"],
    ["sv", "Swedish"],
    ["tr", "Turkish"],
]


@Gtk.Template.from_file(os.path.join(UI_DIR, "preferences.ui"))
class Preferences(Gtk.Dialog):
    __gtype_name__ = "Preferences"

    button_cancel = Gtk.Template.Child()
    button_save = Gtk.Template.Child()
    combobox_language = Gtk.Template.Child()
    entry_installpath = Gtk.Template.Child()

    def __init__(self, parent, config):
        Gtk.Dialog.__init__(self, title="Preferences", parent=parent, modal=True)
        self.__config = config
        self.__set_language_list()
        self.entry_installpath.set_text(config.get("install_dir"))

    def __set_language_list(self):
        languages = Gtk.ListStore(str, str)
        for lang in SUPPORTED_LANGUAGES:
            languages.append(lang)

        self.combobox_language.set_model(languages)
        self.combobox_language.set_entry_text_column(1)
        self.renderer_text = Gtk.CellRendererText()
        self.combobox_language.pack_start(self.renderer_text, False)
        self.combobox_language.add_attribute(self.renderer_text, "text", 1)

        # Set the active option
        current_lang = self.__config.get("lang")
        for key in range(len(languages)):
            if languages[key][:1][0] == current_lang:
                self.combobox_language.set_active(key)
                break

    def __save_language_choice(self):
        lang_choice = self.combobox_language.get_active_iter()
        if lang_choice is not None:
            model = self.combobox_language.get_model()
            lang, _ = model[lang_choice][:2]
            self.__config.set("lang", lang)

    def __save_install_dir_choice(self) -> bool:
        choice = self.entry_installpath.get_text()
        if not os.path.exists(choice):
            try:
                os.makedirs(choice)
            except:
                return False
        else:
            write_test_file = os.path.join(choice, "write_test.txt")
            try:
                with open(write_test_file, "w") as file:
                    file.write("test")
                    file.close()
                os.remove(write_test_file)
            except:
                return False
        self.__config.set("install_dir", choice)
        return True

    @Gtk.Template.Callback("on_button_save_clicked")
    def save_pressed(self, button):
        self.__save_language_choice()
        if self.__save_install_dir_choice():
            self.response(Gtk.ResponseType.OK)
            self.destroy()
        else:
            dialog = Gtk.MessageDialog(
                self,
                0,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                "{} isn't a usable path".format(self.entry_installpath.get_text())
            )
            dialog.run()
            dialog.close()



    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
