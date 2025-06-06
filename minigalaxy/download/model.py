"""Contains different data files and enums used in the download logic"""

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
                 expected_size=None, number=1, out_of_amount=1, game=None,
                 download_icon=None):
        self.url = url
        self.save_location = save_location
        self.__finish_func = finish_func
        self.__progress_func = progress_func
        self.__cancel_func = cancel_func
        self.cancel_reason = None
        self.number = number
        self.out_of_amount = out_of_amount
        self.game = game
        # Type of object, e.g. icon, thumbnail, game, dlc,
        self.download_type = download_type
        self.current_progress = 0
        self.expected_size = expected_size
        self.download_icon = download_icon

    def filename(self):
        return os.path.basename(self.save_location)

    def set_progress(self, percentage: int) -> None:
        "Set the download progress of the Download"
        self.current_progress = percentage
        if self.__progress_func:
            if self.out_of_amount > 1:
                # Change the percentage based on which number we are
                progress_start = 100 / self.out_of_amount * (self.number - 1)
                percentage = progress_start + percentage / self.out_of_amount
                percentage = int(percentage)
            self.__progress_func(percentage)

    def finish(self):
        """
        finish is called when the download has completed
        If a finish_func was specified when the Download was created, call the function
        """
        self.cancel_reason = None  # make sure cancel_reason is reset
        if self.__finish_func:
            try:
                self.__finish_func(self.save_location)
            except (FileNotFoundError, BadZipFile):
                self.cancel()

    def cancel(self):
        "Cancel the download, calling a cancel_func if one was specified"
        if self.__cancel_func:
            self.__cancel_func()

    def on_finish(self, callback):
        if not self.__finish_func and callable(callback):
            self.__finish_func = callback

    def on_cancel(self, callback):
        if not self.__cancel_func and callable(callback):
            self.__cancel_func = callback

    def on_progress(self, callback):
        """Set or remove the progress callback."""
        self.__progress_func = callback

    def __str__(self):
        return self.filename()

    def __repr__(self):
        return self.filename()
