import os

from minigalaxy.css import CSS_PROVIDER
from minigalaxy.game import Game
from minigalaxy.paths import UI_DIR
from minigalaxy.ui.gtk import Gtk
from minigalaxy.ui.library_entry import LibraryEntry


@Gtk.Template.from_file(os.path.join(UI_DIR, "gametilelist.ui"))
class GameTileList(LibraryEntry, Gtk.Box):
    __gtype_name__ = "GameTileList"

    image = Gtk.Template.Child()
    button = Gtk.Template.Child()
    button_cancel = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()
    wine_icon = Gtk.Template.Child()
    update_icon = Gtk.Template.Child()
    menu_button_update = Gtk.Template.Child()
    menu_button_dlc = Gtk.Template.Child()
    menu_button_uninstall = Gtk.Template.Child()
    dlc_horizontal_box = Gtk.Template.Child()
    menu_button_information = Gtk.Template.Child()
    menu_button_properties = Gtk.Template.Child()
    game_label = Gtk.Template.Child()

    def __init__(self, parent_library, game: Game):
        super().__init__(parent_library, game)
        Gtk.Frame.__init__(self)

        self.init_ui_elements()

    def init_ui_elements(self):
        self.__create_progress_bar()
        self.game_label.set_label(self.game.name)
        Gtk.StyleContext.add_provider(self.button.get_style_context(),
                                      CSS_PROVIDER,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        super().init_ui_elements()

    def __create_progress_bar(self) -> None:
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_halign(Gtk.Align.START)
        self.progress_bar.set_size_request(196, -1)
        self.progress_bar.set_hexpand(False)
        self.progress_bar.set_vexpand(False)
        self.progress_bar.set_fraction(0.0)
        self.set_center_widget(self.progress_bar)
        self.progress_bar.hide()

    def __str__(self):
        return self.game.name

    @Gtk.Template.Callback("on_button_clicked")
    def on_button_click(self, widget) -> None:
        super().on_button_primary(widget)

    @Gtk.Template.Callback("on_menu_button_information_clicked")
    def show_information(self, button):
        super().show_information(button)

    @Gtk.Template.Callback("on_menu_button_properties_clicked")
    def show_properties(self, button):
        super().show_properties(button)

    @Gtk.Template.Callback("on_button_cancel_clicked")
    def on_button_cancel(self, widget):
        super().on_button_cancel(widget)

    @Gtk.Template.Callback("on_menu_button_uninstall_clicked")
    def on_menu_button_uninstall(self, widget):
        super().on_button_uninstall(widget)

    @Gtk.Template.Callback("on_menu_button_update_clicked")
    def on_menu_button_update(self, widget):
        super().on_button_update(widget)
