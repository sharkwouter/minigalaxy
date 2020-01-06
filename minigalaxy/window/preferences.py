import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR

SUPPORTED_LANGUAGES = [
    ["br", _("Brazilian Portuguese")],
    ["cn", _("Chinese")],
    ["da", _("Danish")],
    ["nl", _("Dutch")],
    ["en", _("English")],
    ["fi", _("Finnish")],
    ["fr", _("French")],
    ["de", _("German")],
    ["hu", _("Hungarian")],
    ["it", _("Italian")],
    ["jp", _("Japanese")],
    ["ko", _("Korean")],
    ["no", _("Norwegian")],
    ["pl", _("Polish")],
    ["pt", _("Portuguese")],
    ["ru", _("Russian")],
    ["es", _("Spanish")],
    ["sv", _("Swedish")],
    ["tr", _("Turkish")],
]


@Gtk.Template.from_file(os.path.join(UI_DIR, "preferences.ui"))
class Preferences(Gtk.Dialog):
    __gtype_name__ = "Preferences"

    button_cancel = Gtk.Template.Child()
    button_file_chooser = Gtk.Template.Child()
    button_save = Gtk.Template.Child()
    button_stay_logged_in = Gtk.Template.Child()
    combobox_language = Gtk.Template.Child()
    switch_install = Gtk.Template.Child()

    def __init__(self, parent, config):
        Gtk.Dialog.__init__(self, title=_("Preferences"), parent=parent, modal=True)
        self.__config = config
        self.parent = parent
        self.__set_language_list()
        self.button_file_chooser.set_filename(config.get("install_dir"))
        self.switch_install.set_active(self.__config.get("keep_installers"))
        self.button_stay_logged_in.set_active(self.__config.get("stay_logged_in"))

    def __set_language_list(self) -> None:
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

    def __save_language_choice(self) -> None:
        lang_choice = self.combobox_language.get_active_iter()
        if lang_choice is not None:
            model = self.combobox_language.get_model()
            lang, _ = model[lang_choice][:2]
            self.__config.set("lang", lang)

    def __save_install_dir_choice(self) -> bool:
        choice = self.button_file_chooser.get_filename()
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
        # Remove the old directory if it is empty
        old_dir = self.__config.get("install_dir")
        try:
            if old_dir != choice:
                os.rmdir(old_dir)
        except OSError:
            pass

        self.__config.set("install_dir", choice)
        return True

    @Gtk.Template.Callback("on_button_save_clicked")
    def save_pressed(self, button):
        self.__save_language_choice()
        self.__config.set("keep_installers", self.switch_install.get_active())
        self.__config.set("stay_logged_in", self.button_stay_logged_in.get_active())
        if self.__save_install_dir_choice():
            self.response(Gtk.ResponseType.OK)
            self.parent.refresh_game_install_states(path_changed=True)
            self.destroy()
        else:
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=_("{} isn't a usable path").format(self.entry_installpath.get_text())
            )
            dialog.run()
            dialog.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
