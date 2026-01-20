import os
import locale
import shutil
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.constants import SUPPORTED_DOWNLOAD_LANGUAGES, SUPPORTED_LOCALES, VIEWS
from minigalaxy.download_manager import DownloadManager
from minigalaxy.ui.gtk import Gtk
from minigalaxy.config import Config


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
    treeview_translators = Gtk.Template.Child()
    button_add_translator = Gtk.Template.Child()
    button_edit_translator = Gtk.Template.Child()
    button_remove_translator = Gtk.Template.Child()

    def __init__(self, parent, config: Config, download_manager: DownloadManager):
        Gtk.Dialog.__init__(self, title=_("Preferences"), parent=parent, modal=True)
        self.parent = parent
        self.config = config
        self.download_manager = download_manager

        self.__set_locale_list()
        self.__set_language_list()
        self.__set_view_list()
        self.button_file_chooser.set_filename(self.config.install_dir)
        self.switch_keep_installers.set_active(self.config.keep_installers)
        self.switch_stay_logged_in.set_active(self.config.stay_logged_in)
        self.switch_use_dark_theme.set_active(self.config.use_dark_theme)
        self.switch_show_hidden_games.set_active(self.config.show_hidden_games)
        # Setup translators treeview
        self.translator_store = Gtk.ListStore(str, str, str)  # name, type, path
        self.treeview_translators.set_model(self.translator_store)
        for i, title in enumerate([_("Name"), _("Type"), _("Path")]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            self.treeview_translators.append_column(column)
        self.__refresh_translator_list()
        self.button_add_translator.connect("clicked", self.on_add_translator)
        self.button_edit_translator.connect("clicked", self.on_edit_translator)
        self.button_remove_translator.connect("clicked", self.on_remove_translator)

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
        current_locale = self.config.locale
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
        current_lang = self.config.lang
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
        current_view = self.config.view
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
                self.config.locale = locale_choice
            else:
                try:
                    locale.setlocale(locale.LC_ALL, (locale_choice, 'UTF-8'))
                    self.config.locale = locale_choice
                except locale.Error:
                    self.parent.show_error(_("Failed to change program language. Make sure locale is generated on "
                                             "your system."))

    def __save_language_choice(self) -> None:
        lang_choice = self.combobox_language.get_active_iter()
        if lang_choice is not None:
            model = self.combobox_language.get_model()
            lang, _ = model[lang_choice][:2]
            self.config.lang = lang

    def __save_view_choice(self) -> None:
        view_choice = self.combobox_view.get_active_iter()
        if view_choice is not None:
            model = self.combobox_view.get_model()
            view, _ = model[view_choice][:2]
            if view != self.config.view:
                self.parent.reset_library()
            self.config.view = view

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
        self.__save_locale_choice()
        self.__save_language_choice()
        self.__save_view_choice()
        self.__save_theme_choice()
        self.config.keep_installers = self.switch_keep_installers.get_active()
        self.config.stay_logged_in = self.switch_stay_logged_in.get_active()
        self.config.show_hidden_games = self.switch_show_hidden_games.get_active()
        self.config.create_applications_file = self.switch_create_applications_file.get_active()
        self.parent.library.filter_library()

        if self.switch_show_windows_games.get_active() != self.config.show_windows_games:
            if self.switch_show_windows_games.get_active() and not shutil.which("wine"):
                self.parent.show_error(_("Wine wasn't found. Showing Windows games cannot be enabled."))
                self.config.show_windows_games = False
            else:
                self.config.show_windows_games = self.switch_show_windows_games.get_active()
                self.parent.reset_library()

        # Only change the install_dir is it was actually changed


class TranslatorEditDialog(Gtk.Dialog):
    def __init__(self, parent, translator=None):
        Gtk.Dialog.__init__(self, title=_('Translator'), parent=parent, modal=True)
        self.set_default_size(400, 200)
        box = self.get_content_area()
        grid = Gtk.Grid(row_spacing=8, column_spacing=8, margin=12)
        box.add(grid)

        # Name
        grid.attach(Gtk.Label(label=_('Name:')), 0, 0, 1, 1)
        self.entry_name = Gtk.Entry()
        grid.attach(self.entry_name, 1, 0, 1, 1)
        # Type
        grid.attach(Gtk.Label(label=_('Type:')), 0, 1, 1, 1)
        self.combo_type = Gtk.ComboBoxText()
        self.combo_type.append_text('os')
        self.combo_type.append_text('isa')
        grid.attach(self.combo_type, 1, 1, 1, 1)
        # Path
        grid.attach(Gtk.Label(label=_('Path:')), 0, 2, 1, 1)
        self.entry_path = Gtk.Entry()
        grid.attach(self.entry_path, 1, 2, 1, 1)
        # Optional: icon, version, description
        grid.attach(Gtk.Label(label=_('Icon (optional):')), 0, 3, 1, 1)
        self.entry_icon = Gtk.Entry()
        grid.attach(self.entry_icon, 1, 3, 1, 1)
        grid.attach(Gtk.Label(label=_('Version (optional):')), 0, 4, 1, 1)
        self.entry_version = Gtk.Entry()
        grid.attach(self.entry_version, 1, 4, 1, 1)
        grid.attach(Gtk.Label(label=_('Description (optional):')), 0, 5, 1, 1)
        self.entry_description = Gtk.Entry()
        grid.attach(self.entry_description, 1, 5, 1, 1)

        self.add_button(_('Cancel'), Gtk.ResponseType.CANCEL)
        self.add_button(_('OK'), Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        if translator:
            self.entry_name.set_text(translator.get('name', ''))
            self.combo_type.set_active(0 if translator.get('type') == 'os' else 1)
            self.entry_path.set_text(translator.get('path', ''))
            self.entry_icon.set_text(translator.get('icon', ''))
            self.entry_version.set_text(translator.get('version', ''))
            self.entry_description.set_text(translator.get('description', ''))
        else:
            self.combo_type.set_active(0)
        self.show_all()

    def get_translator(self):
        return {
            'name': self.entry_name.get_text(),
            'type': self.combo_type.get_active_text(),
            'path': self.entry_path.get_text(),
            'icon': self.entry_icon.get_text(),
            'version': self.entry_version.get_text(),
            'description': self.entry_description.get_text(),
            'custom': True,
        }
