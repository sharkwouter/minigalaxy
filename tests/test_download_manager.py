import os
import random
import tempfile
from string import ascii_uppercase
from unittest import TestCase
from unittest.mock import MagicMock

from minigalaxy.constants import DOWNLOAD_CHUNK_SIZE
from minigalaxy.download import Download, DownloadType
from minigalaxy.download_manager import DownloadManager


class TestDownloadManager(TestCase):

    def test_download_operation(self):
        session = MagicMock()
        download_request = MagicMock()
        session.get.return_value = download_request

        chunk1 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))
        chunk2 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))
        chunk3 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))

        download_request.iter_content.return_value = [chunk1, chunk2, chunk3]
        download_request.headers.get.return_value = len(chunk1) + len(chunk2) + len(chunk3)
        download_manager = DownloadManager(session)

        progress_func = MagicMock()
        finish_func = MagicMock()
        cancel_func = MagicMock()

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)
        download_manager._DownloadManager__download_operation(download, 0, "wb")

        expected = chunk1 + chunk2 + chunk3
        with open(temp_file) as content:
            actual = content.read().encode('utf-8')
            self.assertEqual(expected, actual)

        # Clean up temp_file
        os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file))

        download_request.headers.get.assert_called_once()
        download_request.iter_content.assert_called_once()

        self.assertEqual(3 + 2, progress_func.call_count)
        self.assertEqual(0, finish_func.call_count)
        self.assertEqual(0, cancel_func.call_count)

    def test_download_operation_still_downloads_without_content_length(self):
        session = MagicMock()
        download_request = MagicMock()
        session.get.return_value = download_request

        chunk1 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))
        chunk2 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))
        chunk3 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))

        download_request.iter_content.return_value = [chunk1, chunk2, chunk3]
        download_request.headers.get.side_effect = TypeError
        download_manager = DownloadManager(session)

        progress_func = MagicMock()
        finish_func = MagicMock()
        cancel_func = MagicMock()

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)
        download_manager._DownloadManager__download_operation(download, 0, "wb")

        expected = chunk1 + chunk2 + chunk3
        with open(temp_file) as content:
            actual = content.read().encode('utf-8')
            self.assertEqual(expected, actual)

        # Clean up temp_file
        os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file))

        download_request.headers.get.assert_called_once()
        download_request.iter_content.assert_called_once()

        self.assertEqual(2, progress_func.call_count)
        self.assertEqual(0, finish_func.call_count)
        self.assertEqual(0, cancel_func.call_count)

    def test_download_operation_cancel_download(self):
        session = MagicMock()
        download_request = MagicMock()
        session.get.return_value = download_request

        chunk1 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))
        chunk2 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))
        chunk3 = bytes(random.choices(ascii_uppercase.encode('utf-8'), k=DOWNLOAD_CHUNK_SIZE))

        download_request.iter_content.return_value = [chunk1, chunk2, chunk3]
        download_request.headers.get.side_effect = TypeError
        download_manager = DownloadManager(session)

        progress_func = MagicMock()
        finish_func = MagicMock()
        cancel_func = MagicMock()

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)
        download_manager.active_downloads[download] = download
        download_manager.cancel_download(download)
        download_manager._DownloadManager__download_operation(download, 0, "wb")

        expected = chunk1
        with open(temp_file) as content:
            actual = content.read().encode('utf-8')
            self.assertEqual(expected, actual)

        # Clean up temp_file
        os.remove(temp_file)
        self.assertFalse(os.path.isfile(temp_file))

        download_request.headers.get.assert_called_once()
        download_request.iter_content.assert_called_once()

        self.assertEqual(1, progress_func.call_count)
        self.assertEqual(0, finish_func.call_count)
        self.assertEqual(0, cancel_func.call_count)

    def test_cancel_download(self):
        session = MagicMock()
        download_manager = DownloadManager(session)

        progress_func = MagicMock()
        finish_func = MagicMock()
        cancel_func = MagicMock()

        temp_file = tempfile.mktemp()
        download = Download("example.com", temp_file, DownloadType.GAME, finish_func, progress_func, cancel_func)

        download_manager.download(download)

        download_manager.cancel_download(download)
        cancel_func.assert_called_once()
        for queue in download_manager.queues:
            for i in queue:
                self.assertNotEqual(i, download)
        self.assertFalse(os.path.isfile(temp_file))
