from dataclasses import dataclass
from typing import Callable, Optional
from zipfile import BadZipFile

from minigalaxy.entity.download_type import DownloadType
from minigalaxy.game import Game


@dataclass
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
    url: str
    save_location: str
    download_type: Optional[DownloadType] = None
    finish_func: Optional[Callable[[str], None]] = None
    progress_func: Optional[Callable[[int], None]] = None
    cancel_func: Optional[Callable[[], None]] = None
    number: int = 1
    out_of_amount: int = 1
    game: Optional[Game] = None

    def set_progress(self, percentage: int) -> None:
        "Set the download progress of the Download"
        if self.progress_func:
            if self.out_of_amount > 1:
                # Change the percentage based on which number we are
                progress_start = 100 / self.out_of_amount * (self.number - 1)
                percentage = progress_start + percentage / self.out_of_amount
                percentage = int(percentage)
            self.progress_func(percentage)

    def finish(self):
        """
        finish is called when the download has completed
        If a finish_func was specified when the Download was created, call the function
        """
        if self.finish_func:
            try:
                self.finish_func(self.save_location)
            except (FileNotFoundError, BadZipFile):
                self.cancel()

    def cancel(self):
        "Cancel the download, calling a cancel_func if one was specified"
        if self.cancel_func:
            self.cancel_func()
