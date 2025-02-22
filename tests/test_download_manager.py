import os
import random
import tempfile
import time
from string import ascii_uppercase
from unittest import TestCase
from unittest.mock import MagicMock

from minigalaxy.constants import DOWNLOAD_CHUNK_SIZE
from minigalaxy.download import Download, DownloadType
from minigalaxy.download_manager import DownloadManager


class TestDownloadManager(TestCase):

    def setUp(self):
        self.session = MagicMock()
        self.config_mock = MagicMock()
        self.config_mock.paused_downloads = {}
        self.download_request = MagicMock()

        self.session.get.return_value = self.download_request

        self.chunks = [
            bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE)),
            bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE)),
            bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))
        ]

        self.download_request.iter_content.return_value = [*self.chunks]
        self.download_request.headers.get.return_value = len(self.chunks) * DOWNLOAD_CHUNK_SIZE
        self.download_manager = DownloadManager(self.session, self.config_mock)
        self.download_manager.fork_listener = False

    def test_download_operation(self):
        progress_func = MagicMock()
        finish_func = MagicMock()
        cancel_func = MagicMock()

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)
        self.download_manager._DownloadManager__download_operation(download, 0, "wb")

        expected = b''.join(self.chunks)
        with open(temp_file) as content:
            actual = content.read().encode('utf-8')
            self.assertEqual(expected, actual)

        # Clean up temp_file
        os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file))

        self.download_request.headers.get.assert_called_once()
        self.download_request.iter_content.assert_called_once()

        # 0 at begin, 33, 66, 100
        self.assertEqual(3 + 1, progress_func.call_count)
        self.assertEqual(0, finish_func.call_count)
        self.assertEqual(0, cancel_func.call_count)

    def test_download_operation_still_downloads_without_content_length(self):
        self.download_request.headers.get.side_effect = TypeError

        progress_func = MagicMock()
        finish_func = MagicMock()
        cancel_func = MagicMock()

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)
        self.download_manager._DownloadManager__download_operation(download, 0, "wb")

        expected = b''.join(self.chunks)
        with open(temp_file) as content:
            actual = content.read().encode('utf-8')
            self.assertEqual(expected, actual)

        # Clean up temp_file
        os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file))

        self.download_request.headers.get.assert_called_once()
        self.download_request.iter_content.assert_called_once()

        self.assertEqual(2, progress_func.call_count)
        self.assertEqual(0, finish_func.call_count)
        self.assertEqual(0, cancel_func.call_count)

    def test_download_operation_cancel_download(self):
        self.download_request.headers.get.side_effect = TypeError

        progress_func = MagicMock()
        finish_func = MagicMock()
        cancel_func = MagicMock()

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)
        self.download_manager.active_downloads[download] = download
        self.download_manager.cancel_download(download)
        self.download_manager._DownloadManager__download_operation(download, 0, "wb")

        expected = self.chunks[0]
        with open(temp_file) as content:
            actual = content.read().encode('utf-8')
            self.assertEqual(expected, actual)

        # Clean up temp_file
        os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file))

        self.download_request.headers.get.assert_called_once()
        self.download_request.iter_content.assert_called_once()

        self.assertEqual(1, progress_func.call_count)
        self.assertEqual(0, finish_func.call_count)
        self.assertEqual(0, cancel_func.call_count)

    def test_cancel_download(self):
        progress_func = MagicMock()
        finish_func = MagicMock()
        finish_func.side_effect = lambda: print("download finished")
        cancel_func = MagicMock()
        cancel_func.side_effect = lambda: print(str(time.time()) + " download cancel received")

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)

        self.download_manager.download(download)

        self.download_manager.cancel_download(download)
        print(str(time.time()) + " assert")
        cancel_func.assert_called_once()
        for queue in self.download_manager.queues:
            for i in queue:
                self.assertNotEqual(i, download)
        self.assertFalse(os.path.isfile(temp_file))
