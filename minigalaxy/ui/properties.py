import urllib
import gi
import os
import subprocess
import webbrowser

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gio
from gi.repository.GdkPixbuf import Pixbuf, InterpType
from minigalaxy.paths import UI_DIR, THUMBNAIL_DIR
from minigalaxy.translation import _
from minigalaxy.launcher import config_game, regedit_game
from minigalaxy.config import Config


@Gtk.Template.from_file(os.path.join(UI_DIR, "properties.ui"))
class Properties(Gtk.Dialog):
    __gtype_name__ = "Properties"
    gogBaseUrl = "https://www.gog.com"

    image = Gtk.Template.Child()
    button_properties_cancel = Gtk.Template.Child()
    button_properties_ok = Gtk.Template.Child()
    button_properties_support = Gtk.Template.Child()
    button_properties_store = Gtk.Template.Child()
    button_properties_open_files = Gtk.Template.Child()
    button_properties_winecfg = Gtk.Template.Child()
    button_properties_regedit = Gtk.Template.Child()
    switch_properties_show_fps = Gtk.Template.Child()
    switch_properties_hide_game = Gtk.Template.Child()
    entry_properties_variable = Gtk.Template.Child()
    entry_properties_command = Gtk.Template.Child()
    label_game_description = Gtk.Template.Child()

    def __init__(self, parent, game, api):
        Gtk.Dialog.__init__(self, title=_("Properties of {}").format(game.name), parent=parent.parent.parent,
                            modal=True)
        self.parent = parent
        self.game = game
        self.api = api
        self.gamesdb_info = self.api.get_gamesdb_info(self.game)

        # Show the image
        self.load_thumbnail()
        self.load_description()

        # Disable/Enable buttons
        self.button_sensitive(game)

        # Retrieve variable & command each time Properties is open
        self.entry_properties_variable.set_text(self.game.get_info("variable"))
        self.entry_properties_command.set_text(self.game.get_info("command"))

        # Keep switch FPS disabled/enabled
        self.switch_properties_show_fps.set_active(self.game.get_info("show_fps"))

        # Keep switch game shown/hidden
        self.switch_properties_hide_game.set_active(self.game.get_info("hide_game"))

    @Gtk.Template.Callback("on_button_properties_cancel_clicked")
    def cancel_pressed(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_ok_clicked")
    def ok_pressed(self, button):
        if self.game.is_installed():
            self.game.set_info("variable", str(self.entry_properties_variable.get_text()))
            self.game.set_info("command", str(self.entry_properties_command.get_text()))
            self.game.set_info("show_fps", self.switch_properties_show_fps.get_active())
        self.game.set_info("hide_game", self.switch_properties_hide_game.get_active())
        self.parent.parent.filter_library()
        self.destroy()

    @Gtk.Template.Callback("on_button_properties_winecfg_clicked")
    def on_menu_button_winecfg(self, widget):
        config_game(self.game)

    @Gtk.Template.Callback("on_button_properties_regedit_clicked")
    def on_menu_button_regedit(self, widget):
        regedit_game(self.game)

    @Gtk.Template.Callback("on_button_properties_open_files_clicked")
    def on_menu_button_open_files(self, widget):
        self.game.set_install_dir()
        subprocess.call(["xdg-open", self.game.install_dir])

    @Gtk.Template.Callback("on_button_properties_support_clicked")
    def on_menu_button_support(self, widget):
        try:
            webbrowser.open(self.api.get_info(self.game)['links']['support'], new=2)
        except webbrowser.Error:
            self.parent.parent.show_error(
                _("Couldn't open support page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_button_properties_store_clicked")
    def on_menu_button_store(self, widget):
        try:
            webbrowser.open(self.gogBaseUrl + self.game.url)
        except webbrowser.Error:
            self.parent.parent.show_error(
                _("Couldn't open store page"),
                _("Please check your internet connection")
            )

    def load_thumbnail(self):
        if self.gamesdb_info["cover"]:
            response = urllib.request.urlopen(self.gamesdb_info["cover"])
            input_stream = Gio.MemoryInputStream.new_from_data(response.read(), None)
            pixbuf = Pixbuf.new_from_stream(input_stream, None)
            pixbuf = pixbuf.scale_simple(340, 480, InterpType.BILINEAR)
            GLib.idle_add(self.image.set_from_pixbuf, pixbuf)
        else:
            thumbnail_path = os.path.join(THUMBNAIL_DIR, "{}.jpg".format(self.game.id))
            if not os.path.isfile(thumbnail_path) and self.game.is_installed:
                thumbnail_path = os.path.join(self.game.install_dir, "thumbnail.jpg")
            GLib.idle_add(self.image.set_from_file, thumbnail_path)

    def load_description(self):
        description = ""
        lang = Config.get("lang")
        if self.gamesdb_info["summary"]:
            desc_lang = "*"
            for summary_key in self.gamesdb_info["summary"].keys():
                if lang in summary_key:
                    desc_lang = summary_key
            description_len = 470
            if len(self.gamesdb_info["summary"][desc_lang]) > description_len:
                description = "{}...".format(self.gamesdb_info["summary"][desc_lang][:description_len])
            else:
                description = self.gamesdb_info["summary"][desc_lang]
            genre_lang = "*"
            for genre_key in self.gamesdb_info["genre"].keys():
                if lang in genre_key:
                    genre_lang = genre_key
            description = "{}: {}\n{}".format(_("Genre"), self.gamesdb_info["genre"][genre_lang], description)
        if self.game.is_installed:
            description = "{}: {}\n{}".format(_("Version"), self.game.get_info("version"), description)
        GLib.idle_add(self.label_game_description.set_text, description)

    def button_sensitive(self, game):
        if not game.is_installed():
            self.button_properties_open_files.set_sensitive(False)
            self.button_properties_winecfg.set_sensitive(False)
            self.entry_properties_command.set_sensitive(False)
            self.entry_properties_variable.set_sensitive(False)
            self.button_properties_regedit.set_sensitive(False)
            self.switch_properties_show_fps.set_sensitive(False)

        if game.platform == 'linux':
            self.button_properties_winecfg.hide()
            self.button_properties_regedit.hide()
