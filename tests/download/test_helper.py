from unittest import TestCase
from unittest.mock import MagicMock

from minigalaxy.download import CombinedProgressWatcher, Download


class TestDownloadHelper(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.actual_progress = None

    def __progress_callback(self, percentage):
        """Helper function used in tests"""
        self.actual_progress = percentage

    def test_no_progress_when_empty(self):
        """[scenario: Empty download list in progress watcher should not trigger callbacks]"""
        watcher = CombinedProgressWatcher(self.__progress_callback, [])
        watcher.list_updated()
        self.assertIsNone(self.actual_progress, "Progress function should not have been called")

    def test_attaches_progress_callback(self):
        """[scenario: progress watcher attaches a customized progress callback to downloads]"""
        download = MagicMock()
        download_list = []
        watcher = CombinedProgressWatcher(self.__progress_callback, download_list)
        download.on_progress.assert_not_called()

        download_list.append(download)
        watcher.list_updated()
        download.on_progress.assert_called_once()

    def test_progress_tracked_individually(self):
        """[scenario: progress watcher keeps track of each file via progress callbacks]"""
        download1 = Download("localhost:8080/abc", "abc.temp")
        download2 = Download("localhost:8080/def", "def.temp")
        download_list = [download1, download2]

        watcher = CombinedProgressWatcher(self.__progress_callback, download_list)

        expected_progress = {
            download1: 0,
            download2: 0
        }

        # check that all downloads are initialized with 0
        self.assertEqual(expected_progress, watcher.download_progress)

        download2.set_progress(50)

        self.assertEqual(25, self.actual_progress, "Should have received a progress update")

        # make sure only the second download has been updated
        expected_progress[download2] = 50
        self.assertEqual(expected_progress, watcher.download_progress)

    def test_add_new_downloads(self):
        """[scenario: adding new downloads also dynamically recalculates current progress]"""
        download1 = Download("localhost:8080/abc", "abc.temp")
        download2 = Download("localhost:8080/def", "def.temp")
        download_list = [download1, download2]

        watcher = CombinedProgressWatcher(self.__progress_callback, download_list)
        download2.set_progress(100)

        # add more, with 0 progress
        download3 = Download("localhost:8080/123", "123.temp")
        download4 = Download("localhost:8080/456", "456.temp")
        download_list.extend([download3, download4])
        watcher.list_updated()

        # now we have 0 / 100 / 0 / 0, which is 100/5 = 25 total progress
        self.assertEqual(25, self.actual_progress, "Adding new downloads should have reduced overall progress")
        expected_progress_states = {
            download1: 0,
            download2: 100,
            download3: 0,
            download4: 0,
        }
        self.assertEqual(expected_progress_states, watcher.download_progress, "Must have updated download progress states")

    def test_remove_downloads(self):
        """[scenario: removing downloads updates current and deregisters progress listener]"""
        download1 = Download("localhost:8080/abc", "abc.temp")
        download2 = Download("localhost:8080/def", "def.temp")
        download3 = Download("localhost:8080/123", "123.temp")
        download_list = [download1, download2, download3]

        watcher = CombinedProgressWatcher(self.__progress_callback, download_list)
        download1.set_progress(100)
        download2.set_progress(100)
        self.assertEqual(66, self.actual_progress, "Progress calculation should be integers")

        download_list.remove(download2)
        watcher.list_updated()

        self.assertEqual(download_list, [*watcher.download_progress.keys()])
        self.assertIsNone(download2._Download__progress_func)
        self.assertEqual(50, self.actual_progress, "Removing a download must update progress")

        # emptying the list should fall back to 0 progress
        download_list.clear()
        watcher.list_updated()
        self.assertEqual(0, self.actual_progress)

    def test_update_list_mixed(self):
        """[scenario: updating the list must be able to handle add and remove at once]"""

        download1 = Download("localhost:8080/abc", "abc.temp")
        download2 = Download("localhost:8080/def", "def.temp")
        download3 = Download("localhost:8080/123", "123.temp")
        download4 = Download("localhost:8080/456", "456.temp")

        download_list = [download1, download2, download3]
        watcher = CombinedProgressWatcher(self.__progress_callback, download_list)

        download3.set_progress(100)
        self.assertEqual(33, self.actual_progress)

        # change the list
        download_list.remove(download3)
        download_list.append(download4)
        watcher.list_updated()
        self.assertEqual(0, self.actual_progress)

        expected_progress_states = {
            download1: 0,
            download2: 0,
            download4: 0
        }
        self.assertEqual(expected_progress_states, watcher.download_progress)

    def test_properties(self):
        """[scenario: make sure the property accessors are correct]"""

        download1 = Download("localhost:8080/abc", "abc.temp")
        download2 = Download("localhost:8080/def", "def.temp")
        download3 = Download("localhost:8080/123", "123.temp")

        download_list = [download1, download2, download3]
        watcher = CombinedProgressWatcher(self.__progress_callback, download_list)

        download1.set_progress(12)
        download2.set_progress(88)
        download3.set_progress(54)

        expected_progress_values = [12, 88, 54]

        self.assertEqual(expected_progress_values, [*watcher.progress_list])
        self.assertEqual(3, watcher.num_downloads)
