"""
A DownloadManager that provides an interface to manage and retry downloads.

First, you need to create a Download object, then pass the Download object to the
DownloadManager to download it.

Example:
>>> import os
>>> from minigalaxy.download import Download
>>> from minigalaxy.download_manager import DownloadManager
>>> def your_function():
>>>   image_url = "https://www.gog.com/bundles/gogwebsitestaticpages/images/icon_section1-header.png"
>>>   thumbnail = os.path.join(".", "{}.jpg".format("test-icon"))
>>>   download = Download(image_url, thumbnail, finish_func=lambda x: print("Done downloading {}!".format(x)))
>>>   DownloadManager.download(download)
>>> your_function() # doctest: +SKIP
"""
import logging
import os
import shutil
import time
import threading
import queue

from requests.exceptions import RequestException
from minigalaxy.config import Config
from minigalaxy.constants import DOWNLOAD_CHUNK_SIZE, MINIMUM_RESUME_SIZE, SESSION, NUMBER_DOWNLOAD_THREADS
from minigalaxy.download import Download
import minigalaxy.logger

module_logger = logging.getLogger("minigalaxy.download_manager")

class QueuedDownloadItem:
    """
    Wrap downloads in a simple class so we can manage when to download them
    """
    def __init__(self, download, priority=1):
        """
        Create a QueuedDownloadItem with a given download and priority level
        """
        self.priority = priority
        self.item = download
        self.queue_time = time.time_ns()

    def __lt__(self, other):
        """
        Only compare QueuedDownloadItems on their priority level and
        time added to the queue.
        Later versions might use other factors (size, download type, etc.)
        For example, UX needs might want to prioritize items and other UI assets.
        """
        if self.priority != other.priority:
            return self.priority < other.priority
        else:
            return self.queue_time < other.queue_time

class __DownloadManger:
    """
    A DownloadManager that provides an interface to manage and retry downloads.

    First, you need to create a Download object, then pass the Download object to the
    DownloadManager download or download_now method to download it.
    """
    def __init__(self):
        """
        Create a new DownloadManager Object

        Args:
            This initializer takes no arguments
        """
        # The Queue to store items for download
        self.__queue = queue.PriorityQueue()
        self.__cancel = {}
        self.__paused = False
        self.workers = []
        # The list of currently active downloads
        self.active_downloads = {}
        self.active_downloads_lock = threading.Lock()

        self.logger = logging.getLogger("minigalaxy.download_manager.DownloadManager")

        for i in range(NUMBER_DOWNLOAD_THREADS):
            download_thread = threading.Thread(target=lambda: self.__download_thread(i))
            download_thread.id = i
            download_thread.daemon = True
            download_thread.start()
            self.workers.append(download_thread)

    def download(self, download):
        """
        Add a download or list of downloads to the queue for downloading
        You can download a single Download or a list of Downloads

        Args:
            A single Download or a list of Download objects
        """
        if isinstance(download, Download):
            self.__queue.put(QueuedDownloadItem(download))
        else:
            # Assume we've received a list of downloads
            for d in download:
                self.__queue.put(QueuedDownloadItem(d))

    def download_now(self, download):
        """
        Download an item with a higher priority
        Any item with the download_now priority set will get downloaded
        before other items.

        This is useful for things like thumbnails and icons that are important
        for UX responsiveness.

        Args:
            The Download to download
        """
        self.__queue.put(QueuedDownloadItem(download, 0))

    def cancel_download(self, downloads):
        """
        Cancel a download or a list of downloads

        Args:
            A single Download or a list of Download objects
        """
        self.logger.debug("Canceling download: {}".format(downloads))
        # Make sure we're always dealing with a list
        if isinstance(downloads, Download):
            downloads = [downloads]

        for download in downloads:
            with self.active_downloads_lock:
                if download in self.active_downloads:
                    self.logger.debug("Found download")
                    self.__cancel[download] = True
                else:
                    self.__paused = True
                    new_queue = queue.PriorityQueue()
                    while not self.__queue.empty():
                        queued_download = self.__queue.get()
                        if download == queued_download.item:
                            download.cancel()
                        elif download.game == queued_download.item.game:
                            download.cancel()
                        else:
                            new_queue.put(queued_download)
                        # Mark the task as "done" to keep counts correct so
                        # we can use join() or other functions later
                        self.__queue.task_done()
                    self.__queue = new_queue
                    self.__paused = False

    def cancel_current_downloads(self):
        """
        Cancel the currentl downloads
        """
        self.logger.debug("Canceling current download")
        with self.active_downloads_lock:
            for download in self.active_downloads:
                self.__cancel[download] = True

    def cancel_all_downloads(self):
        """
        Cancel all current downloads queued
        """
        self.logger.debug("Canceling all downloads")
        self.logger.debug("queue length: {}".format(self.__queue.qsize()))
        while not self.__queue.empty():
            download = self.__queue.get().item
            self.logger.debug("canceling another download: {}".format(download.save_location))
            # Mark the task as "done" to keep counts correct so
            # we can use join() or other functions later
            self.__queue.task_done()
        self.cancel_current_downloads()

    def __remove_download_from_active_downloads(self, download):
        "Remove a download from the list of active downloads"
        with self.active_downloads_lock:
            if download in self.active_downloads:
                self.logger.debug("Removing download from active downloads list")
                del self.active_downloads[download]
            else:
                self.logger.debug("Didn't find download in active downloads list")

    def __download_thread(self, id=0):
        """
        The main DownloadManager thread calls this when it is created
        It checks the queue, starting new downloads when they are available
        Users of this library should not need to call this.
        """
        while True:
            if not self.__queue.empty():
                # Update the active downloads
                with self.active_downloads_lock:
                    download = self.__queue.get().item
                    self.active_downloads[download] = download
                self.__download_file(download, id)
                # Mark the task as done to keep counts correct so
                # we can use join() or other functions later
                self.__queue.task_done()
            time.sleep(0.1)

    def __download_file(self, download, id=0):
        """
        This is called by __download_thread to download a file
        It is also called directly by the thread created in download_now
        Users of this library should not need to call this.

        Args:
            The Download to download
        """
        self.__prepare_location(download.save_location)
        download_max_attempts = 5
        download_attempt = 0
        result = False
        while download_attempt < download_max_attempts:
            try:
                start_point, download_mode = self.__get_start_point_and_download_mode(download)
                result = self.__download_operation(download, start_point, download_mode)
                break
            except RequestException as e:
                print(e)
                download_attempt += 1
        # Successful downloads
        if result:
            if download.number == download.out_of_amount:
                self.logger.debug("Download finished, thread {}".format(id))
                finish_thread = threading.Thread(target=download.finish)
                finish_thread.start()
            self.__remove_download_from_active_downloads(download)
            if self.__queue.empty():
                Config.unset("current_downloads")
        # Unsuccessful downloads and cancels
        else:
            if download in self.__cancel:
                del self.__cancel[download]
            download.cancel()
            self.__remove_download_from_active_downloads(download)
            os.remove(download.save_location)
            # We may want to unset current_downloads here
            # For example, if a download was added that is impossible to complete

    def __prepare_location(self, save_location):
        """
        Make sure the download directory exists and the file doesn't already exist

        Args:
            A filename string, where the download should be saved
        """
        # Make sure the directory exists
        save_directory = os.path.dirname(save_location)
        if not os.path.isdir(save_directory):
            os.makedirs(save_directory, mode=0o755)

        # Fail if the file already exists
        if os.path.isdir(save_location):
            shutil.rmtree(save_location)
            self.logger.debug("{} is a directory. Will remove it, to make place for installer.".format(save_location))

    def __get_start_point_and_download_mode(self, download):
        """
        Resume the previous download if possible

        Args:
            The Download to download
        """
        start_point = 0
        download_mode = 'wb'
        if os.path.isfile(download.save_location):
            if self.__is_same_download_as_before(download):
                self.logger.debug("Resuming download {}".format(download.save_location))
                download_mode = 'ab'
                start_point = os.stat(download.save_location).st_size
            else:
                os.remove(download.save_location)
        return start_point, download_mode

    def __download_operation(self, download, start_point, download_mode):
        """
        Download the file
        This is called by __download_file to actually perform the download

        Args:
            The Download to download
            The start point in the download, specified in bytes
            The file mode to save the file as.
              For example, "wb" to create a new file
              or "ab" to append to a file for download resumes
        """
        resume_header = {'Range': 'bytes={}-'.format(start_point)}
        download_request = SESSION.get(download.url, headers=resume_header, stream=True, timeout=30)
        downloaded_size = start_point
        file_size = int(download_request.headers.get('content-length'))
        result = True
        if downloaded_size < file_size:
            with open(download.save_location, download_mode) as save_file:
                for chunk in download_request.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    # Pause if needed
                    while self.__paused:
                        time.sleep(0.1)
                    save_file.write(chunk)
                    downloaded_size += len(chunk)
                    if download in self.__cancel:
                        self.logger.debug("Canceling download: {}".format(download.save_location))
                        result = False
                        del self.__cancel[download]
                        break
                    if file_size > 0:
                        progress = int(downloaded_size / file_size * 100)
                        download.set_progress(progress)
                save_file.close()
        else:
            download.set_progress(100)
        self.logger.debug("Returning result from _download_operation: {}".format(result))
        return result

    def __is_same_download_as_before(self, download):
        """
        Return true if the download is the same as an item with the same save_location
        already downloaded.

        Args:
            The Download to check
        """
        file_stats = os.stat(download.save_location)
        # Don't resume for very small files
        if file_stats.st_size < MINIMUM_RESUME_SIZE:
            return False

        # Check if the first part of the file
        download_request = SESSION.get(download.url, stream=True)
        size_to_check = DOWNLOAD_CHUNK_SIZE * 5
        for chunk in download_request.iter_content(chunk_size=size_to_check):
            with open(download.save_location, "rb") as file:
                file_content = file.read(size_to_check)
                return file_content == chunk

DownloadManager = __DownloadManger()
