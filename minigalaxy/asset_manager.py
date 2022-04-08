from datetime import datetime, timedelta
from enum import Enum
import os
from pathlib import PurePath
import urllib
from minigalaxy.download import Download
from minigalaxy.download_manager import DownloadManager
from minigalaxy.paths import COVER_DIR, THUMBNAIL_DIR
from minigalaxy.ui.gtk import Gio, GdkPixbuf


class ItemNotCachedError(Exception):
    """Raised when an item is not found or not cached"""
    pass


class AssetType(Enum):
    ICON = 1
    THUMBNAIL = 2
    COVER = 3


class Asset:
    """
    Class for a single asset such as a thumbnail
    This class provides methods for checking if an asset already exists in the filesystem
    and whether it's expired.
    """
    def __init__(self, asset_type, url, extra={}):
        """
        Create a new asset
        The constructor accepts two required arguments and an optional argument
        The first argument is the AssetType, such as AssetType.THUMBNAIL
        The second argument is the URL of the asset to download
        The third argument is optional data that can be used to construct
        the filename or alternate sources.
        """
        self.asset_type = asset_type
        self.url = url
        self.extra = extra
        self.build_filename()

    def url_file_extension(self):
        """
        Get the file extension from the URL path extension
        """
        if self.url:
            url_path = urllib.parse.urlparse(self.url).path
            file_path = PurePath(url_path)
            extension = file_path.suffix.lstrip(".")
            return extension
        else:
            return None

    def build_filename(self):
        """
        Build the filename from the AssetType and image URL
        """
        if self.asset_type == AssetType.COVER:
            if "game_id" in self.extra:
                extension = self.url_file_extension()
                if extension:
                    self.filename = os.path.join(COVER_DIR, "{}.{}".format(
                        self.extra["game_id"], extension))
                else:
                    self.filename = None
            if "game_installed" in self.extra and self.extra["game_installed"] and "game_install_dir" in self.extra:
                self.alt_filename = os.path.join(self.extra["game_install_dir"], "cover.jpg")

    def exists(self):
        "Return True if the file exists"
        if self.filename:
            return os.path.exists(self.filename)
        else:
            return False

    def modified_time(self):
        "Return the last modified time (mtime) of the asset"
        try:
            t = datetime.fromtimestamp(os.stat(self.filename).st_mtime)
            return t
        except FileNotFoundError:
            raise ItemNotCachedError(self.filename)

    def expired(self):
        "Return True if an item is expired, otherwise return False"
        elapsed = datetime.now() - self.modified_time()
        return elapsed > timedelta(days=1)


class AssetManager:
    """
    Manage a set of assets such as icons, thumbnails, games and DLC
    This class handles downloading, caching, resizing, saving and loading assets.

    This class has one main method that users should call after creating the object:

    Example:
      asset = Asset(AssetType.COVER, self.gamesdb_info["cover"],
                      { "game_id": self.api_info[0]["id"],
                        "game_installed": False
                       })
      am = AssetManager(asset)
      am.load(draw_callback)

    Where draw_callback is a function or method that accepts a Gtk pixbuf
    """
    def __init__(self, asset):
        """
        Construct the AssetManager with a single Asset
        """
        self.asset = asset

    def create_asset_dirs():
        """
        Class method to create the asset directories

        Example:
        AssetManager.create_asset_dirs()
        """
        # Create the thumbnails directory
        if not os.path.exists(THUMBNAIL_DIR):
            os.makedirs(THUMBNAIL_DIR, mode=0o755)

        # Create the covers directory
        if not os.path.exists(COVER_DIR):
            os.makedirs(COVER_DIR, mode=0o755)

    def load(self, draw_callback):
        """
        Load an asset and call a callback to draw the pixbuf
        If the image isn't cached, download it, resize it, save it and display it
        If the image is cached, load the file and display it

        Users of this class should pass in a function that accepts a Gtk pixbuf argument
        The class will pass in the asset after loading it.
        """
        self.__draw = draw_callback

        # Using a try except pattern for cache misses simplifies the logic a bit
        try:
            if self.asset.exists():
                if self.asset.expired():
                    raise ItemNotCachedError
                else:
                    self.__load_asset()
            else:
                # Case where the asset doesn't exist on the filesystem
                raise ItemNotCachedError
        except ItemNotCachedError:
            if self.asset.url:
                self.download_asset()
            else:
                # If there is no URL, we can try using the installed game
                # thumbnail
                self.__load_alternate_asset()

    def download_thumbnail(self):
        response = urllib.request.urlopen(self.asset.url)
        input_stream = Gio.MemoryInputStream.new_from_data(response.read(), None)
        pixbuf = GdkPixbuf.Pixbuf.new_from_stream(input_stream, None)
        pixbuf = pixbuf.scale_simple(340, 480, GdkPixbuf.InterpType.BILINEAR)

    def download_asset(self):
        """
        Download an asset image
        After downloading, the asset is resized, saved and drawn to the window
        """
        download = Download(self.asset.url, self.asset.filename,
                            finish_func=self.__resize_asset)
        DownloadManager.download_now(download)

    def __resize_asset(self, save_location):
        """
        Resize a asset image
        After resizing, the asset is saved and drawn to the window
        """
        if not os.path.isfile(self.asset.filename):
            return
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.asset.filename)
        pixbuf = pixbuf.scale_simple(340, 480, GdkPixbuf.InterpType.BILINEAR)
        self.__save_asset(pixbuf)

    def __save_asset(self, pixbuf):
        """
        Save an asset image
        After saving, the asset is drawn to the window
        """
        extension = self.asset.url_file_extension()
        pixbuf.savev(self.asset.filename, extension)
        self.__draw(pixbuf)

    def __load_asset(self):
        """
        Load an asset image
        After getting the filename, the asset loaded and drawn to the window
        """
        asset_path = self.asset.filename
        if not os.path.isfile(asset_path):
            self.__load_alternate_asset()
        else:
            self.__load_file(asset_path)

    def __load_alternate_asset(self):
        """
        Load an alternate asset if one is available
        """
        if self.asset.alt_filename:
            asset_path = self.asset.alt_filename
            if not os.path.isfile(asset_path):
                return
            self.__load_file(asset_path)

    def __load_file(self, asset_path):
        "Finally load the asset from the filesystem and call the callback with the pixbuf"
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(asset_path)
            self.__draw(pixbuf)
        except FileNotFoundError:
            return
