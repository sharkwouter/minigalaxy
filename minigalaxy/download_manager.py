import os
import time
import threading
import queue
import requests
from minigalaxy.constants import DOWNLOAD_CHUNK_SIZE


class __DownloadManger:
    def __init__(self):
        self.__queue = queue.Queue()
        self.__current_download = None
        self.__cancel = False

        download_thread = threading.Thread(target=self.__download_thread)
        download_thread.daemon = True
        download_thread.start()

    def download(self, download):
        self.__queue.put(download)

    def download_now(self, download):
        download_file_thread = threading.Thread(target=self.__download_file, args=download)
        download_file_thread.daemon = True
        download_file_thread.start()

    def cancel_current_download(self):
        self.__cancel = True

    def __download_thread(self):
        while True:
            if not self.__queue.empty():
                self.__download_file(self.__queue.get())
            time.sleep(0.1)

    def __download_file(self, download):
        # Make sure the directory exists
        save_directory = os.path.dirname(download.save_location)
        if not os.path.isdir(save_directory):
            os.makedirs(save_directory)

        # Fail if the file already exists
        if os.path.isdir(download.save_location):
            raise IsADirectoryError("{} is a directory".format(download.save_location))
        if os.path.isfile(download.save_location):
            os.remove(download.save_location)

        # Download the file
        download_request = requests.get(download.url, stream=True)
        downloaded_size = 0
        file_size = int(download_request.headers.get('content-length'))
        with open(download.save_location, 'wb') as save_file:
            for chunk in download_request.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
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
        download.finish()


DownloadManager = __DownloadManger()
