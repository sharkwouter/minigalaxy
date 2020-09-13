import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
import shutil
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.constants import SUPPORTED_DOWNLOAD_LANGUAGES
from minigalaxy.config import Config


@Gtk.Template.from_file(os.path.join(UI_DIR, "preferences.ui"))
class Preferences(Gtk.Dialog):
    __gtype_name__ = "Preferences"

    combobox_language = Gtk.Template.Child()
    button_file_chooser = Gtk.Template.Child()
    label_keep_installers = Gtk.Template.Child()
    switch_keep_installers = Gtk.Template.Child()
    switch_stay_logged_in = Gtk.Template.Child()
    switch_show_fps = Gtk.Template.Child()
    switch_show_windows_games = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    button_save = Gtk.Template.Child()

    def __init__(self, parent, download_manager):
        Gtk.Dialog.__init__(self, title=_("Preferences"), parent=parent, modal=True)
        self.parent = parent
        self.__download_manager = download_manager
        self.__set_language_list()
        self.button_file_chooser.set_filename(Config.get("install_dir"))
        self.switch_keep_installers.set_active(Config.get("keep_installers"))
        self.switch_stay_logged_in.set_active(Config.get("stay_logged_in"))
        self.switch_show_fps.set_active(Config.get("show_fps"))
        self.switch_show_windows_games.set_active(Config.get("show_windows_games"))

        # Set tooltip for keep installers label
        installer_dir = os.path.join(self.button_file_chooser.get_filename(), "installer")
        self.label_keep_installers.set_tooltip_text(
            _("Keep installers after downloading a game.\nInstallers are stored in: {}").format(installer_dir)
        )

        # Only allow showing Windows games if wine is available
        if not shutil.which("wine"):
            self.switch_show_windows_games.set_sensitive(False)
            self.switch_show_windows_games.set_tooltip_text(
                _("Install Wine to enable this feature")
            )

    def __set_language_list(self) -> None:
        languages = Gtk.ListStore(str, str)
        for lang in SUPPORTED_DOWNLOAD_LANGUAGES:
            languages.append(lang)

        self.combobox_language.set_model(languages)
        self.combobox_language.set_entry_text_column(1)
        self.renderer_text = Gtk.CellRendererText()
        self.combobox_language.pack_start(self.renderer_text, False)
        self.combobox_language.add_attribute(self.renderer_text, "text", 1)

        # Set the active option
        current_lang = Config.get("lang")
        for key in range(len(languages)):
            if languages[key][:1][0] == current_lang:
                self.combobox_language.set_active(key)
                break

    def __save_language_choice(self) -> None:
        lang_choice = self.combobox_language.get_active_iter()
        if lang_choice is not None:
            model = self.combobox_language.get_model()
            lang, _ = model[lang_choice][:2]
            Config.set("lang", lang)

    def __save_install_dir_choice(self) -> bool:
        choice = self.button_file_chooser.get_filename()
        old_dir = Config.get("install_dir")
        if choice == old_dir:
            return True

        if not os.path.exists(choice):
            try:
                os.makedirs(choice, mode=0o755)
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
        try:
            os.rmdir(old_dir)
        except OSError:
            pass

        Config.set("install_dir", choice)
        return True

    @Gtk.Template.Callback("on_button_save_clicked")
    def save_pressed(self, button):
        self.__save_language_choice()
        Config.set("keep_installers", self.switch_keep_installers.get_active())
        Config.set("stay_logged_in", self.switch_stay_logged_in.get_active())
        Config.set("show_fps", self.switch_show_fps.get_active())

        if self.switch_show_windows_games.get_active() != Config.get("show_windows_games"):
            Config.set("show_windows_games", self.switch_show_windows_games.get_active())
            self.parent.reset_library()

        # Only change the install_dir is it was actually changed
        if self.button_file_chooser.get_filename() != Config.get("install_dir"):
            if self.__save_install_dir_choice():
                self.__download_manager.cancel_all_downloads()
                self.parent.reset_library()
            else:
                dialog = Gtk.MessageDialog(
                    parent=self,
                    modal=True,
                    destroy_with_parent=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=_("{} isn't a usable path").format(self.button_file_chooser.get_filename())
                )
                dialog.run()
                dialog.destroy()
        self.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
