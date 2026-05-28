from gi.repository import Gdk
from minigalaxy.entity.state import State
from minigalaxy.game import Game
from minigalaxy.resources import platform_name_to_icon_file
from minigalaxy.ui.gtk import Gtk, load_ui, load_scaled_pixbuf


@Gtk.Template(string=load_ui("game_icon_bar.ui"))
class GameIconBar(Gtk.Box):
    __gtype_name__ = "GameIconBar"

    update_icon = Gtk.Template.Child()
    lnx_icon = Gtk.Template.Child()
    wine_icon = Gtk.Template.Child()

    def __init__(self, parent_gametile, game: Game):
        Gtk.Box.__init__(self)

        self.parent_gametile = parent_gametile
        self.config = parent_gametile.config
        self.game = game
        self.clickable = False

        self.__load_scaled_icon(self.lnx_icon, "linux")
        self.__load_scaled_icon(self.wine_icon, "windows")

    @Gtk.Template.Callback()
    def toggle_image_highlight(self, icon: Gtk.Image, event):
        """Used to highlight platform selection icons when hovering over them. Shows a pretty border."""

        if not self.clickable:
            return

        style = icon.get_style_context()
        if event.type == Gdk.EventType.LEAVE_NOTIFY and style.has_class("icon-highlight"):
            style.remove_class("icon-highlight")
        elif event.type == Gdk.EventType.ENTER_NOTIFY:
            style.add_class("icon-highlight")

    @Gtk.Template.Callback()
    def platform_icon_bar_clicked(self, icon: Gtk.Image, event):
        """
        Used to change/override platform selection where supported.
        Only works if clicking on an icon would make sense (there are multiple choices).

        FIXME: The current implementation is commented out party because the required background logic
        for platform change is not complete yet.
        """
        if not self.clickable or event.type != event.type == Gdk.EventType.BUTTON_PRESS:
            return

        """
        new_selection = self.update_selected_icon(icon.get_name())
        self.parent_gametile.update_platform_choice(new_selection)
        """

    def update_icon_state(self, game_state):
        for icon in [self.lnx_icon, self.wine_icon]:
            # the icon GtkImage.name property is used to link the instances to the platform they represent
            if icon.get_name() == self.game.platform:
                icon.show()
            else:
                icon.hide()
        self.reset_selected_icons()

        if game_state == State.UPDATABLE:
            self.update_icon.show()
        else:
            self.update_icon.hide()

    def reset_selected_icons(self):
        """Deselects all platform icons. Useful for a fresh start of just the UI."""
        for icon in [self.lnx_icon, self.wine_icon]:
            icon.get_style_context().remove_class("active-platform")

    def update_selected_icon(self, platform_name):
        """
        Detects a change in platform from one to the other OR deselection of the currently selected platform.
        Returns the name of the new selection or None in case of deselection
        """
        new_selection = None
        for icon in [self.lnx_icon, self.wine_icon]:
            style = icon.get_style_context()
            if icon.get_name() == platform_name and not style.has_class("active-platform"):
                new_selection = platform_name
                style.add_class("active-platform")
            else:
                style.remove_class("active-platform")

        return new_selection

    def __load_scaled_icon(self, icon_holder: Gtk.Image, platform):
        icon_file = platform_name_to_icon_file(platform)
        pixbuf = load_scaled_pixbuf(icon_file, Gtk.IconSize.lookup(Gtk.IconSize.SMALL_TOOLBAR)[1])
        icon_holder.set_from_pixbuf(pixbuf)
