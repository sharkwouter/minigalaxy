import os

from enum import Enum
from zipfile import BadZipFile


# Enums were added in Python 3.4
class DownloadType(Enum):
    ICON = 1
    THUMBNAIL = 2
    GAME = 3
    GAME_UPDATE = 4
    GAME_DLC = 5


class Download:
    """
    A class to easily download from URLs and save the file.

    Usage:
    >>> import os
    >>> from minigalaxy.download import Download, DownloadType
    >>> from minigalaxy.download_manager import DownloadManager
    >>> def your_function():
    >>>   image_url = "https://www.gog.com/bundles/gogwebsitestaticpages/images/icon_section1-header.png"
    >>>   thumbnail = os.path.join(".", "{}.jpg".format("test-icon"))
    >>>   download = Download(image_url, thumbnail, DownloadType.THUMBNAIL, finish_func=lambda x: print("Done downloading {}!".format(x))) # noqa: E501
    >>> your_function() # doctest: +SKIP
    """

    def __init__(self, url, save_location, download_type=None,
                 finish_func=None, progress_func=None, cancel_func=None,
                 expected_size=None, game=None, download_icon=None):
        self.url = url
        self.save_location = save_location
        self.callback_complete = finish_func
        self.callback_progress = progress_func
        self.callback_cancel = cancel_func
        self.game = game
        # Type of object, e.g. icon, thumbnail, game, dlc,
        self.download_type = download_type
        self.current_progress = -1
        self.expected_size = expected_size
        self.download_icon = download_icon

    def filename(self):
        return os.path.basename(self.save_location)

    def set_progress(self, percentage: int) -> None:
        "Set the download progress of the Download"
        if percentage <= self.current_progress:
            return

        self.current_progress = percentage
        if self.callback_progress:
            self.callback_progress(percentage)

    def finish(self, result=None):
        """
        finish is called when the download has completed
        If a finish_func was specified when the Download was created, call the function
        """
        if self.callback_complete:
            if not result:
                result = self.save_location
            try:
                self.callback_complete(result)
            except (FileNotFoundError, BadZipFile):
                self.cancel()

    def cancel(self):
        "Cancel the download, calling a cancel_func if one was specified"
        if self.callback_cancel:
            self.callback_cancel()
