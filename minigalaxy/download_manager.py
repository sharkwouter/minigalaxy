import os
import time
import threading
import queue
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

    def cancel_download(self, download):
        if download == self.__current_download:
            self.cancel_current_download()
        else:
            self.__paused = True
            new_queue = queue.Queue()
            while not self.__queue.empty():
                queued_download = self.__queue.get()
                if download == queued_download:
                    download.cancel()
                else:
                    new_queue.put(queued_download)
            self.__queue = new_queue
            self.__paused = False

    def cancel_current_download(self):
        self.__cancel = True

    def __download_thread(self):
        while True:
            if not self.__queue.empty():
                self.__current_download = self.__queue.get()
                self.__download_file(self.__current_download)
            time.sleep(0.1)

    def __download_file(self, download):
        # Make sure the directory exists
        save_directory = os.path.dirname(download.save_location)
        if not os.path.isdir(save_directory):
            os.makedirs(save_directory)

        # Fail if the file already exists
        if os.path.isdir(download.save_location):
            raise IsADirectoryError("{} is a directory".format(download.save_location))

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

        # Download the file
        resume_header = {'Range': 'bytes={}-'.format(start_point)}
        download_request = SESSION.get(download.url, headers=resume_header, stream=True)
        downloaded_size = start_point
        file_size = int(download_request.headers.get('content-length'))
        with open(download.save_location, download_mode) as save_file:
            for chunk in download_request.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                # Pause if needed
                while self.__paused:
                    time.sleep(0.1)
                save_file.write(chunk)
                downloaded_size += len(chunk)
                if self.__cancel:
                    self.__cancel = False
                    save_file.close()
                    download.cancel()
                    return
                if file_size > 0:
                    progress = int(downloaded_size / file_size * 100)
                    download.set_progress(progress)
            save_file.close()
        finish_thread = threading.Thread(target=download.finish)
        finish_thread.start()

    def __is_same_download_as_before(self, download):
        file_stats = os.stat(download.save_location)
        # Don't resume for very small files
        if file_stats.st_size < MINIMUM_RESUME_SIZE:
            return False

        # Check if the first part of the file
        download_request = SESSION.get(download.url, stream=True)
        size_to_check = DOWNLOAD_CHUNK_SIZE*5
        for chunk in download_request.iter_content(chunk_size=size_to_check):
            with open(download.save_location, "rb") as file:
                file_content = file.read(size_to_check)
                return file_content == chunk


DownloadManager = __DownloadManger()
