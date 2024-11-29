import os
import locale

from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.constants import SUPPORTED_DOWNLOAD_LANGUAGES, SUPPORTED_LOCALES, VIEWS, WINE_VARIANTS
from minigalaxy.download_manager import DownloadManager
from minigalaxy.ui.gtk import Gtk
from minigalaxy.config import Config
from minigalaxy.wine_utils import is_wine_installed


@Gtk.Template.from_file(os.path.join(UI_DIR, "preferences.ui"))
class Preferences(Gtk.Dialog):
    __gtype_name__ = "Preferences"

    combobox_program_language = Gtk.Template.Child()
    combobox_language = Gtk.Template.Child()
    combobox_view = Gtk.Template.Child()
    combobox_wine_variant = Gtk.Template.Child()
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

    def __init__(self, parent, config: Config, download_manager: DownloadManager):
        Gtk.Dialog.__init__(self, title=_("Preferences"), parent=parent, modal=True)
        self.parent = parent
        self.config = config
        self.download_manager = download_manager

        self.__init_combobox(self.combobox_program_language, SUPPORTED_LOCALES, self.config.locale)
        self.__init_combobox(self.combobox_language, SUPPORTED_DOWNLOAD_LANGUAGES, self.config.lang)
        self.__init_combobox(self.combobox_view, VIEWS, self.config.view)
        self.__init_combobox(self.combobox_wine_variant, WINE_VARIANTS, self.config.default_wine_runner)

        self.button_file_chooser.set_filename(self.config.install_dir)
        self.switch_keep_installers.set_active(self.config.keep_installers)
        self.switch_stay_logged_in.set_active(self.config.stay_logged_in)
        self.switch_use_dark_theme.set_active(self.config.use_dark_theme)
        self.switch_show_hidden_games.set_active(self.config.show_hidden_games)
        self.switch_show_windows_games.set_active(self.config.show_windows_games)
        self.switch_create_applications_file.set_active(self.config.create_applications_file)

        # Set tooltip for keep installers label
        installer_dir = os.path.join(self.button_file_chooser.get_filename(), "installer")
        self.label_keep_installers.set_tooltip_text(
            _("Keep installers after downloading a game.\nInstallers are stored in: {}").format(installer_dir)
        )

    def __init_combobox(self, combobox, data_feed, active_option) -> None:
        """expects 2-dimensional array with 2 columns for data
        first entry per row is the config key, second one the string to display in the UI
        """
        datalist = Gtk.ListStore(str, str)
        for entry in data_feed:
            datalist.append(entry)

        combobox.set_model(datalist)
        combobox.set_entry_text_column(1)
        # renderer can't be shared, no need to put it into a class member
        renderer_text = Gtk.CellRendererText()
        combobox.pack_start(renderer_text, False)
        combobox.add_attribute(renderer_text, "text", 1)

        # Set the active option
        for key in range(len(datalist)):
            if datalist[key][:1][0] == active_option:
                combobox.set_active(key)
                break

    def __save_combo_value(self, combobox, prop_name) -> bool:
        """puts current value (first array element in model for selection) into config[prop_name]
        returns true if the value has changed"""
        active_choice = combobox.get_active_iter()
        current_config = getattr(self.config, prop_name)
        value = current_config
        if active_choice is not None:
            model = combobox.get_model()
            value, _ = model[active_choice][:2]
            setattr(self.config, prop_name, value)
        return value != current_config

    def __save_locale_choice(self) -> None:
        current_locale = self.config.locale
        if self.__save_combo_value(self.combobox_program_language, 'locale'):
            new_locale = self.config.locale
            if new_locale == '':
                new_locale = locale.getdefaultlocale()[0]

            try:
                locale.setlocale(locale.LC_ALL, (new_locale, 'UTF-8'))
            except locale.Error:
                self.config.locale = current_locale
                self.parent.show_error(_("Failed to change program language. Make sure locale is generated on "
                                         "your system."))

    def __save_theme_choice(self) -> None:
        settings = Gtk.Settings.get_default()
        self.config.use_dark_theme = self.switch_use_dark_theme.get_active()
        if self.config.use_dark_theme is True:
            settings.set_property("gtk-application-prefer-dark-theme", True)
        else:
            settings.set_property("gtk-application-prefer-dark-theme", False)

    def __save_install_dir_choice(self) -> bool:
        choice = self.button_file_chooser.get_filename()
        old_dir = self.config.install_dir
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

        self.config.install_dir = choice
        return True

    @Gtk.Template.Callback("on_button_save_clicked")
    def save_pressed(self, button):
        library_reset_needed = False

        # comboboxes
        self.__save_locale_choice()
        self.__save_combo_value(self.combobox_language, 'lang')
        self.__save_combo_value(self.combobox_wine_variant, 'default_wine_runner')
        library_reset_needed = self.__save_combo_value(self.combobox_view, 'view')

        # on/off switches
        self.__save_theme_choice()
        self.config.keep_installers = self.switch_keep_installers.get_active()
        self.config.stay_logged_in = self.switch_stay_logged_in.get_active()
        self.config.show_hidden_games = self.switch_show_hidden_games.get_active()
        self.config.create_applications_file = self.switch_create_applications_file.get_active()
        self.parent.library.filter_library()

        if self.switch_show_windows_games.get_active() != self.config.show_windows_games:
            if self.switch_show_windows_games.get_active() and not is_wine_installed():
                self.parent.show_error(_("Wine wasn't found. Showing Windows games cannot be enabled."))
                self.config.show_windows_games = False
            else:
                self.config.show_windows_games = self.switch_show_windows_games.get_active()
                library_reset_needed = True

        # Only change the install_dir if it was actually changed
        if self.button_file_chooser.get_filename() != self.config.install_dir:
            if self.__save_install_dir_choice():
                self.download_manager.cancel_all_downloads()
                library_reset_needed = True
            else:
                self.parent.show_error(_("{} isn't a usable path").format(self.button_file_chooser.get_filename()))

        if library_reset_needed:
            self.parent.reset_library()

        self.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
