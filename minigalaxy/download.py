from zipfile import BadZipFile


class Download:
    """
    A class to easily download from URLs and save the file.

    Usage:
    >>> import os
    >>> from minigalaxy.download import Download
    >>> from minigalaxy.download_manager import DownloadManager
    >>> def your_function():
    >>>   image_url = "https://www.gog.com/bundles/gogwebsitestaticpages/images/icon_section1-header.png"
    >>>   thumbnail = os.path.join(".", "{}.jpg".format("test-icon"))
    >>>   download = Download(image_url, thumbnail, finish_func=lambda x: print("Done downloading {}!".format(x)))
    >>> your_function() # doctest: +SKIP


    """
    def __init__(self, url, save_location, finish_func=None, progress_func=None, cancel_func=None, number=1,
                 out_of_amount=1, game=None):
        self.url = url
        self.save_location = save_location
        self.__finish_func = finish_func
        self.__progress_func = progress_func
        self.__cancel_func = cancel_func
        self.number = number
        self.out_of_amount = out_of_amount
        self.game = game

    def set_progress(self, percentage: int) -> None:
        "Set the download progress of the Download"
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
        if self.__finish_func:
            try:
                self.__finish_func(self.save_location)
            except (FileNotFoundError, BadZipFile):
                self.cancel()

    def cancel(self):
        "Cancel the download, calling a cancel_func if one was specified"
        if self.__cancel_func:
            self.__cancel_func()
