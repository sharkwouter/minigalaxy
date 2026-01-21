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

    def state_updating(self):
        # You can customize this as needed, or call the parent implementation
        super().state_updating()
