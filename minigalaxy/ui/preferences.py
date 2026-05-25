import logging
import os
import locale
import shutil

from minigalaxy.config import Config
from minigalaxy.constants import PLATFORM_MODE, SUPPORTED_DOWNLOAD_LANGUAGES, SUPPORTED_LOCALES, VIEWS
from minigalaxy.download_manager import DownloadManager
from minigalaxy.translation import _
from minigalaxy.ui.gtk import Gtk, load_ui
from minigalaxy.ui.widget_utils import get_combo_value, populate_combobox


@Gtk.Template(string=load_ui("preferences.ui"))
class Preferences(Gtk.Dialog):
    __gtype_name__ = "Preferences"

    combobox_program_language = Gtk.Template.Child()
    combobox_language = Gtk.Template.Child()
    combobox_view = Gtk.Template.Child()
    combobox_platform_mode = Gtk.Template.Child()
    button_file_chooser = Gtk.Template.Child()
    label_keep_installers = Gtk.Template.Child()
    switch_keep_installers = Gtk.Template.Child()
    switch_stay_logged_in = Gtk.Template.Child()
    switch_show_hidden_games = Gtk.Template.Child()
    switch_create_applications_file = Gtk.Template.Child()
    switch_use_dark_theme = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    button_save = Gtk.Template.Child()

    def __init__(self, parent, config: Config, download_manager: DownloadManager):
        Gtk.Dialog.__init__(self, title=_("Preferences"), parent=parent, modal=True)
        self.parent = parent
        self.config = config
        self.download_manager = download_manager

        self.__set_locale_list()
        self.__set_language_list()
        self.__set_view_list()
        populate_combobox(self.combobox_platform_mode, PLATFORM_MODE, self.config._raw_platform_mode())
        self.button_file_chooser.set_filename(self.config.install_dir)
        self.switch_keep_installers.set_active(self.config.keep_installers)
        self.switch_stay_logged_in.set_active(self.config.stay_logged_in)
        self.switch_use_dark_theme.set_active(self.config.use_dark_theme)
        self.switch_show_hidden_games.set_active(self.config.show_hidden_games)
        self.switch_create_applications_file.set_active(self.config.create_applications_file)

        # Set tooltip for keep installers label
        installer_dir = os.path.join(self.button_file_chooser.get_filename(), "installer")
        self.label_keep_installers.set_tooltip_text(
            _("Keep installers after downloading a game.\nInstallers are stored in: {}").format(installer_dir)
        )

    def __set_locale_list(self) -> None:
        # Set the active option
        current_locale = self.config.locale
        default_locale = locale.getdefaultlocale()
        if current_locale is None:
            locale.setlocale(locale.LC_ALL, default_locale)

        populate_combobox(self.combobox_program_language, SUPPORTED_LOCALES, current_locale)

    def __set_language_list(self) -> None:
        populate_combobox(self.combobox_language, SUPPORTED_DOWNLOAD_LANGUAGES, self.config.lang)

    def __set_view_list(self) -> None:
        populate_combobox(self.combobox_view, VIEWS, self.config.view)

    def __apply_locale_choice(self) -> None:
        locale_choice = get_combo_value(self.combobox_program_language)
        if locale_choice == '' or not locale_choice:
            locale_choice = locale.getdefaultlocale()[0]

        try:
            locale.setlocale(locale.LC_ALL, (locale_choice, 'UTF-8'))
            self.config.locale = locale_choice
        except locale.Error:
            self.parent.show_error(_("Failed to change program language. Make sure locale is generated on your system."))

    def __apply_view_choice(self) -> None:
        view = get_combo_value(self.combobox_view)
        if view != self.config.view:
            self.parent.reset_library()
        self.config.view = view

    def __apply_theme_choice(self) -> None:
        settings = Gtk.Settings.get_default()
        self.config.use_dark_theme = self.switch_use_dark_theme.get_active()
        if self.config.use_dark_theme != settings.get_property("gtk-application-prefer-dark-theme"):
            settings.set_property("gtk-application-prefer-dark-theme", self.config.use_dark_theme)

    def __apply_platform_mode(self):
        new_mode = get_combo_value(self.combobox_platform_mode)
        if new_mode == self.config._raw_platform_mode():
            return
        self.config.platform_mode = new_mode
        self.parent.reset_library()
        if "windows" in new_mode and not shutil.which("wine"):
            self.parent.show_error(_("Wine wasn't found. Windows games will be shown but not be installable."))

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
        save_changes = True
        try:
            self.config.start_batch_edit()

            self.__apply_locale_choice()
            self.config.lang = get_combo_value(self.combobox_language)
            self.__apply_view_choice()
            self.__apply_theme_choice()
            self.config.keep_installers = self.switch_keep_installers.get_active()
            self.config.stay_logged_in = self.switch_stay_logged_in.get_active()
            self.config.show_hidden_games = self.switch_show_hidden_games.get_active()
            self.config.create_applications_file = self.switch_create_applications_file.get_active()
            self.parent.library.filter_library()

            self.__apply_platform_mode()

            # Only change the install_dir is it was actually changed
            if self.button_file_chooser.get_filename() != self.config.install_dir:
                if self.__save_install_dir_choice():
                    self.download_manager.cancel_all_downloads()
                    self.parent.reset_library()
                else:
                    self.parent.show_error(_("{} isn't a usable path").format(self.button_file_chooser.get_filename()))

        except Exception as e:
            logging.error("Could not save preferences", exc_info=1)
            self.config.cancel_batch_edit()
            save_changes = False
            self.parent.show_error(_("There was an error while saving preferences."), str(e))

        if save_changes:
            self.config.save()

        self.destroy()

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def cancel_pressed(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        self.destroy()
