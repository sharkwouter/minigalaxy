import os

from minigalaxy.game import Game
from minigalaxy.paths import UI_DIR
from minigalaxy.ui.gtk import Gtk
from minigalaxy.ui.library_entry import LibraryEntry


@Gtk.Template.from_file(os.path.join(UI_DIR, "gametile.ui"))
class GameTile(LibraryEntry, Gtk.Box):
    __gtype_name__ = "GameTile"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    os_translator_icon = Gtk.Template.Child()
    isa_translator_icon = Gtk.Template.Child()
    update_icon = Gtk.Template.Child()
    menu_button_update = Gtk.Template.Child()
    menu_button_dlc = Gtk.Template.Child()
    menu_button_uninstall = Gtk.Template.Child()
    dlc_scroll_panel = Gtk.Template.Child()
    dlc_horizontal_box = Gtk.Template.Child()
    menu_button_information = Gtk.Template.Child()
    menu_button_properties = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()

    def __init__(self, parent_library, game: Game):
        super().__init__(parent_library, game)
        Gtk.Frame.__init__(self)

        self.init_ui_elements()

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        super().run_primary_action(widget)

    @Gtk.Template.Callback("on_menu_button_information_clicked")
    def show_information(self, button):
        super().show_information(button)

    @Gtk.Template.Callback("on_menu_button_properties_clicked")
    def show_properties(self, button):
        super().show_properties(button)

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def on_button_cancel(self, widget):
        super().confirm_and_cancel_download(widget)

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        super().confirm_and_uninstall(widget)

    @Gtk.Template.Callback("on_menu_button_update_clicked")
    def on_menu_button_update(self, widget):
        super().run_update(widget)

    @Gtk.Template.Callback("recalculate_dlc_list_size")
    def recalc_dlc_list_size(self, widget, *data):
        super().recalc_dlc_list_size(self.dlc_scroll_panel, self.dlc_horizontal_box)

    def state_installed(self):
        self.menu_button.get_style_context().add_class("suggested-action")
        super().state_installed()

    def state_uninstalling(self):
        # Set translator icons
        from minigalaxy.config import Config
        config = Config()
        selected = self.game.get_selected_translators(config)
        translators = {t["name"]: t for t in config.translators}
        # OS Translator icon
        os_icon = None
        os_name = selected.get("os")
        if os_name and os_name in translators:
            os_icon = translators[os_name].get("icon")
        if os_icon and os.path.isfile(os_icon):
            self.os_translator_icon.set_from_file(os_icon)
        else:
            self.os_translator_icon.set_from_icon_name("applications-system", Gtk.IconSize.SMALL_TOOLBAR)
        # ISA Translator icon
        isa_icon = None
        isa_name = selected.get("isa")
        if isa_name and isa_name in translators:
            isa_icon = translators[isa_name].get("icon")
        if isa_icon and os.path.isfile(isa_icon):
            self.isa_translator_icon.set_from_file(isa_icon)
        else:
            self.isa_translator_icon.set_from_icon_name("applications-engineering", Gtk.IconSize.SMALL_TOOLBAR)

    def state_updating(self):
        # You can customize this as needed, or call the parent implementation
        super().state_updating()
