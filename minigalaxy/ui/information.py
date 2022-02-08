import urllib
import os
import webbrowser

from minigalaxy.paths import UI_DIR, THUMBNAIL_DIR, COVER_DIR
from minigalaxy.translation import _
from minigalaxy.config import Config
from minigalaxy.download import Download
from minigalaxy.download_manager import DownloadManager
from minigalaxy.ui.gtk import Gtk, GLib, Gio, GdkPixbuf


@Gtk.Template.from_file(os.path.join(UI_DIR, "information.ui"))
class Information(Gtk.Dialog):
    __gtype_name__ = "Information"
    gogBaseUrl = "https://www.gog.com"

    image = Gtk.Template.Child()
    button_information_ok = Gtk.Template.Child()
    button_information_support = Gtk.Template.Child()
    button_information_store = Gtk.Template.Child()
    button_information_forum = Gtk.Template.Child()
    button_information_gog_database = Gtk.Template.Child()
    button_information_pcgamingwiki = Gtk.Template.Child()
    label_game_description = Gtk.Template.Child()

    def __init__(self, parent, game, api):
        Gtk.Dialog.__init__(self, title=_("Information about {}").format(game.name), parent=parent.parent.parent,
                            modal=True)
        self.parent = parent
        self.game = game
        self.api = api
        self.gamesdb_info = self.api.get_gamesdb_info(self.game)

        # Show the image
        self.load_thumbnail()
        self.load_description()

        # Center information window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

    @Gtk.Template.Callback("on_button_information_ok_clicked")
    def ok_pressed(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_information_support_clicked")
    def on_menu_button_support(self, widget):
        try:
            webbrowser.open(self.api.get_info(self.game)['links']['support'], new=2)
        except webbrowser.Error:
            self.parent.parent.show_error(
                _("Couldn't open support page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_button_information_store_clicked")
    def on_menu_button_store(self, widget):
        try:
            webbrowser.open(self.gogBaseUrl + self.game.url)
        except webbrowser.Error:
            self.parent.parent.show_error(
                _("Couldn't open store page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_button_information_forum_clicked")
    def on_menu_button_forum(self, widget):
        try:
            webbrowser.open(self.api.get_info(self.game)['links']['forum'], new=2)
        except webbrowser.Error:
            self.parent.parent.show_error(
                _("Couldn't open forum page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_button_information_gog_database_clicked")
    def on_menu_button_gog_database(self, widget):
        try:
            webbrowser.open("https://www.gogdb.org/product/{}".format(self.game.id))
        except webbrowser.Error:
            self.parent.parent.show_error(
                _("Couldn't open forum page"),
                _("Please check your internet connection")
            )

    @Gtk.Template.Callback("on_button_information_pcgamingwiki_clicked")
    def on_menu_button_pcgamingwiki(self, widget):
        try:
            webbrowser.open("https://pcgamingwiki.com/api/gog.php?page={}".format(self.game.id))
        except webbrowser.Error:
            self.parent.parent.show_error(
                _("Couldn't open forum page"),
                _("Please check your internet connection")
            )

    def load_thumbnail(self):
        if self.gamesdb_info["cover"]:
            cover_path = os.path.join(COVER_DIR, "{}.jpg".format(self.game.id))
            if os.path.isfile(cover_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(cover_path)
                pixbuf = pixbuf.scale_simple(340, 480, GdkPixbuf.InterpType.BILINEAR)
                GLib.idle_add(self.image.set_from_pixbuf, pixbuf)
            else:
                url = "{}".format(self.gamesdb_info["cover"])
                download = Download(url, cover_path)
                DownloadManager.download_now(download)
                response = urllib.request.urlopen(url)
                input_stream = Gio.MemoryInputStream.new_from_data(response.read(), None)
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(input_stream, None)
                pixbuf = pixbuf.scale_simple(340, 480, GdkPixbuf.InterpType.BILINEAR)
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
            if "*" in self.gamesdb_info["genre"]:
                genre = self.gamesdb_info["genre"]["*"]
            else:
                genre = _("unknown")
            for genre_key, genre_value in self.gamesdb_info["genre"].items():
                if lang in genre_key:
                    genre = genre_value
            description = "{}: {}\n{}".format(_("Genre"), genre, description)
        if self.game.is_installed():
            description = "{}: {}\n{}".format(_("Version"), self.game.get_info("version"), description)
        GLib.idle_add(self.label_game_description.set_text, description)
