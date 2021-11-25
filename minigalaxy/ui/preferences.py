import os
import locale
import shutil
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.constants import SUPPORTED_DOWNLOAD_LANGUAGES, SUPPORTED_LOCALES, VIEWS
from minigalaxy.config import Config
from minigalaxy.download_manager import DownloadManager
from minigalaxy.ui.gtk import Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "preferences.ui"))
class Preferences(Gtk.Dialog):
    __gtype_name__ = "Preferences"

    combobox_program_language = Gtk.Template.Child()
    combobox_language = Gtk.Template.Child()
    combobox_view = Gtk.Template.Child()
    button_file_chooser = Gtk.Template.Child()
    label_keep_installers = Gtk.Template.Child()
    switch_keep_installers = Gtk.Template.Child()
    switch_stay_logged_in = Gtk.Template.Child()
    switch_show_hidden_games = Gtk.Template.Child()
    switch_show_windows_games = Gtk.Template.Child()
    switch_create_applications_file = Gtk.Template.Child()
    switch_use_dark_theme = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    button_save = Gtk.Template.Child()

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title=_("Preferences"), parent=parent, modal=True)
        self.parent = parent

        self.__set_locale_list()
        self.__set_language_list()
        self.__set_view_list()
        self.button_file_chooser.set_filename(Config.get("install_dir"))
        self.switch_keep_installers.set_active(Config.get("keep_installers"))
        self.switch_stay_logged_in.set_active(Config.get("stay_logged_in"))
        self.switch_use_dark_theme.set_active(Config.get("use_dark_theme"))
        self.switch_show_hidden_games.set_active(Config.get("show_hidden_games"))
        self.switch_show_windows_games.set_active(Config.get("show_windows_games"))
        self.switch_create_applications_file.set_active(Config.get("create_applications_file"))

        # Set tooltip for keep installers label
        installer_dir = os.path.join(self.button_file_chooser.get_filename(), "installer")
        self.label_keep_installers.set_tooltip_text(
            _("Keep installers after downloading a game.\nInstallers are stored in: {}").format(installer_dir)
        )

    def __set_locale_list(self) -> None:
        locales = Gtk.ListStore(str, str)
        for local in SUPPORTED_LOCALES:
            locales.append(local)

        self.combobox_program_language.set_model(locales)
        self.combobox_program_language.set_entry_text_column(1)
        self.renderer_text = Gtk.CellRendererText()
        self.combobox_program_language.pack_start(self.renderer_text, False)
        self.combobox_program_language.add_attribute(self.renderer_text, "text", 1)

        # Set the active option
        current_locale = Config.get("locale")
        default_locale = locale.getdefaultlocale()
        if current_locale is None:
            locale.setlocale(locale.LC_ALL, default_locale)
        for key in range(len(locales)):
            if locales[key][:1][0] == current_locale:
                self.combobox_program_language.set_active(key)
                break

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

    def __set_view_list(self) -> None:
        views = Gtk.ListStore(str, str)
        for view in VIEWS:
            views.append(view)

        self.combobox_view.set_model(views)
        self.combobox_view.set_entry_text_column(1)
        self.renderer_text = Gtk.CellRendererText()
        self.combobox_view.pack_start(self.renderer_text, False)
        self.combobox_view.add_attribute(self.renderer_text, "text", 1)

        # Set the active option
        current_view = Config.get("view")
        for key in range(len(views)):
            if views[key][:1][0] == current_view:
                self.combobox_view.set_active(key)
                break

    def __save_locale_choice(self) -> None:
        new_locale = self.combobox_program_language.get_active_iter()
        if new_locale is not None:
            model = self.combobox_program_language.get_model()
            locale_choice = model[new_locale][-2]
            if locale_choice == '':
                default_locale = locale.getdefaultlocale()[0]
                locale.setlocale(locale.LC_ALL, (default_locale, 'UTF-8'))
                Config.set("locale", locale_choice)
            else:
                try:
                    locale.setlocale(locale.LC_ALL, (locale_choice, 'UTF-8'))
                    Config.set("locale", locale_choice)
                except locale.Error:
                    self.parent.show_error(_("Failed to change program language. Make sure locale is generated on "
                                             "your system."))

    def __save_language_choice(self) -> None:
        lang_choice = self.combobox_language.get_active_iter()
        if lang_choice is not None:
            model = self.combobox_language.get_model()
            lang, _ = model[lang_choice][:2]
            Config.set("lang", lang)

    def __save_view_choice(self) -> None:
        view_choice = self.combobox_view.get_active_iter()
        if view_choice is not None:
            model = self.combobox_view.get_model()
            view, _ = model[view_choice][:2]
            if view != Config.get("view"):
                self.parent.reset_library()
            Config.set("view", view)

    def __save_theme_choice(self) -> None:
        settings = Gtk.Settings.get_default()
        Config.set("use_dark_theme", self.switch_use_dark_theme.get_active())
        if Config.get("use_dark_theme") is True:
            settings.set_property("gtk-application-prefer-dark-theme", True)
        else:
            settings.set_property("gtk-application-prefer-dark-theme", False)

    def __save_install_dir_choice(self) -> bool:
        choice = self.button_file_chooser.get_filename()
        old_dir = Config.get("install_dir")
        if choice == old_dir:
            return True

        if not os.path.exists(choice):
            try:
                os.makedirs(choice, mode=0o755)
            except Exception:
                return False
        else:
            write_test_file = os.path.join(choice, "write_test.txt")
            try:
                with open(write_test_file, "w") as file:
                    file.write("test")
                    file.close()
                os.remove(write_test_file)
            except Exception:
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
        self.__save_locale_choice()
        self.__save_language_choice()
        self.__save_view_choice()
        self.__save_theme_choice()
        Config.set("keep_installers", self.switch_keep_installers.get_active())
        Config.set("stay_logged_in", self.switch_stay_logged_in.get_active())
        Config.set("show_hidden_games", self.switch_show_hidden_games.get_active())
        Config.set("create_applications_file", self.switch_create_applications_file.get_active())
        self.parent.library.filter_library()

        if self.switch_show_windows_games.get_active() != Config.get("show_windows_games"):
            if self.switch_show_windows_games.get_active() and not shutil.which("wine"):
                self.parent.show_error(_("Wine wasn't found. Showing Windows games cannot be enabled."))
                Config.set("show_windows_games", False)
            else:
                Config.set("show_windows_games", self.switch_show_windows_games.get_active())
                self.parent.reset_library()

        # Only change the install_dir is it was actually changed
        if self.button_file_chooser.get_filename() != Config.get("install_dir"):
            if self.__save_install_dir_choice():
                DownloadManager.cancel_all_downloads()
                self.parent.reset_library()
            else:
                self.parent.show_error(_("{} isn't a usable path").format(self.button_file_chooser.get_filename()))
        self.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
