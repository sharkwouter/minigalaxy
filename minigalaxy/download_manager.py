import os
import shutil
import time
import threading
import queue

from requests.exceptions import ConnectionError
from minigalaxy.config import Config
from minigalaxy.constants import DOWNLOAD_CHUNK_SIZE, MINIMUM_RESUME_SIZE, SESSION
from minigalaxy.download import Download


class __DownloadManger:
    def __init__(self):
        self.__queue = queue.Queue()
        self.__current_download = None
        self.__cancel = False
        self.__paused = False

        download_thread = threading.Thread(target=self.__download_thread)
        download_thread.daemon = True
        download_thread.start()

    def download(self, download):
        if isinstance(download, Download):
            self.__queue.put(download)
        else:
            # Assume we've received a list of downloads
            for d in download:
                self.__queue.put(d)

    def download_now(self, download):
        download_file_thread = threading.Thread(target=self.__download_file, args=(download,))
        download_file_thread.daemon = True
        download_file_thread.start()

    def cancel_download(self, downloads):
        # Make sure we're always dealing with a list
        if isinstance(downloads, Download):
            downloads = [downloads]

        for download in downloads:
            if download == self.__current_download:
                self.cancel_current_download()
            else:
                self.__paused = True
                new_queue = queue.Queue()
                while not self.__queue.empty():
                    queued_download = self.__queue.get()
                    if download == queued_download:
                        download.cancel()
                    elif download.game == queued_download.game:
                        download.cancel()
                    else:
                        new_queue.put(queued_download)
                self.__queue = new_queue
                self.__paused = False

    def cancel_current_download(self):
        self.__cancel = True

    def cancel_all_downloads(self):
        while not self.__queue.empty():
            self.__queue.get()
        self.cancel_current_download()

        # wait for the download to be fully cancelled
        while self.__current_download:
            time.sleep(0.1)

    def __download_thread(self):
        while True:
            if not self.__queue.empty():
                self.__current_download = self.__queue.get()
                self.__download_file(self.__current_download)
            time.sleep(0.1)

    def __download_file(self, download):
        self.prepare_location(download.save_location)
        download_max_attempts = 5
        download_attempt = 0
        result = False
        while download_attempt < download_max_attempts:
            try:
                start_point, download_mode = self.get_start_point_and_download_mode(download)
                result = self.download_operation(download, start_point, download_mode)
                break
            except ConnectionError as e:
                print(e)
                download_attempt += 1
        # Successful downloads
        if result:
            if download.number == download.out_of_amount:
                finish_thread = threading.Thread(target=download.finish)
                finish_thread.start()
            if self.__queue.empty():
                Config.unset("current_download")
        # Unsuccessful downloads and cancels
        else:
            self.__cancel = False
            download.cancel()
            self.__current_download = None
            os.remove(download.save_location)

    def prepare_location(self, save_location):
        # Make sure the directory exists
        save_directory = os.path.dirname(save_location)
        if not os.path.isdir(save_directory):
            os.makedirs(save_directory, mode=0o755)

        # Fail if the file already exists
        if os.path.isdir(save_location):
            shutil.rmtree(save_location)
            print("{} is a directory. Will remove it, to make place for installer.".format(save_location))

    def get_start_point_and_download_mode(self, download):
        # Resume the previous download if possible
        start_point = 0
        download_mode = 'wb'
        if os.path.isfile(download.save_location):
            if self.__is_same_download_as_before(download):
                print("Resuming download {}".format(download.save_location))
                download_mode = 'ab'
                start_point = os.stat(download.save_location).st_size
            else:
                os.remove(download.save_location)
        return start_point, download_mode

    def download_operation(self, download, start_point, download_mode):
        # Download the file
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
                    if self.__cancel:
                        result = False
                        break
                    if file_size > 0:
                        progress = int(downloaded_size / file_size * 100)
                        download.set_progress(progress)
                save_file.close()
        else:
            download.set_progress(100)
        return result

    def __is_same_download_as_before(self, download):
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
