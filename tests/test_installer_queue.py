import time

from unittest import TestCase, mock
from unittest.mock import MagicMock
from threading import RLock, Thread

from minigalaxy.game import Game
from minigalaxy import installer


class Test(TestCase):

    def test_no_duplicates(self):
        '''[scenario: InstallerQueue.put() must ignore items which are equal to already placed items.]'''
        lock = RLock()  # use inserted lock to prevent the installer thread from picking items
        test_queue = installer.InstallerQueue(lock)

        # use try-finally because of queue.clear() to stop worker
        try:
            items_to_put = [32, "something", 32, "another", "another"]
            lock.acquire()

            for i in items_to_put:
                test_queue.put(i)

            self.assertEqual(3, len(test_queue.queue), "There should be 3 items with no duplicates on the queue")
            self.assertEqual([32, "something", "another"], [*test_queue.queue])
        finally:
            test_queue.queue.clear()
            lock.release()

    def test_install_thread_lifecycle(self):
        '''[scenario: The install worker thread of InstallerQueue must only run when there are items on the queue]'''
        lock = RLock()  # use inserted lock to prevent the installer thread from picking items
        test_queue = installer.InstallerQueue(lock)
        self.assertIsNone(test_queue.worker, "Worker thread should not be spawned by default")

        # use try-finally because of queue.clear() to stop worker
        try:
            lock.acquire()
            item = MagicMock()
            test_queue.put(item)
            self.assertIsInstance(test_queue.worker, Thread)
            self.assertTrue(test_queue.worker.is_alive(), "worker thread should be assigned and alive after put")
            spawned_worker = test_queue.worker

            # let the worker thread do its work
            lock.release()
            time.sleep(0.5)

            # then take the lock again
            lock.acquire()

            item.execute.assert_called_once()

            # worker must be dead and gone
            self.assertTrue(test_queue.empty(), "Queue should be empty again")
            self.assertFalse(spawned_worker.is_alive(), "Worker thread should be dead when the queue is empty")
            self.assertIsNone(test_queue.worker, "Worker thread should be gone")
        finally:
            test_queue.queue.clear()
            lock.release()

    @mock.patch('minigalaxy.installer.InstallerQueue')
    def test_enqueue_game_install_lazy_init(self, mock_queue_class):
        '''[scenario: The very first invocation of installer.enqueue_game_install creates the global InstallerQueue]'''

        installer.INSTALL_QUEUE = None

        queue_instance = MagicMock()
        mock_queue_class.return_value = queue_instance

        self.assertIsNone(installer.INSTALL_QUEUE, "Global INSTALL_QUEUE must not exist yet")
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky")
        installer.enqueue_game_install("42", MagicMock(), game, "/path/to/installer")

        self.assertIs(queue_instance, installer.INSTALL_QUEUE)
        queue_instance.put.assert_called_once()

    @mock.patch('minigalaxy.installer.install_game')
    def test_enqueue_game(self, mock_install):
        """[scenario: Game gets queued and ultimately runs into install_game]"""

        installer.INSTALL_QUEUE = None
        result_callback = MagicMock()

        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        installer.enqueue_game_install(12345, result_callback,
                                       game, installer="adrift.exe", language="", install_dir="",
                                       keep_installers=False, create_desktop_file=True)
        time.sleep(0.5)
        lock = installer.INSTALL_QUEUE.state_lock
        with lock:
            mock_install.assert_called_once()
            result_callback.assert_called_once()

            name, args, kwargs = result_callback.mock_calls[-1]
            install_result = args[0]
            self.assertEqual(installer.InstallResultType.SUCCESS, install_result.type)
            self.assertEqual("/home/makson/GOG Games/Absolute Drift", install_result.reason)

    @mock.patch('minigalaxy.installer.install_game')
    def test_enqueue_game_failure(self, mock_install):
        """[scenario: Game gets queued and ultimately runs into install_game]"""

        installer.INSTALL_QUEUE = None
        result_callback = MagicMock()
        mock_install.side_effect = installer.InstallException("error")

        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform="windows")
        installer.enqueue_game_install(12345, result_callback,
                                       game, installer="adrift.exe", language="", install_dir="",
                                       keep_installers=False, create_desktop_file=True)
        time.sleep(0.5)
        lock = installer.INSTALL_QUEUE.state_lock
        with lock:
            mock_install.assert_called_once()
            result_callback.assert_called_once()

            name, args, kwargs = result_callback.mock_calls[-1]
            install_result = args[0]
            self.assertEqual(installer.InstallResultType.FAILURE, install_result.type)
            self.assertEqual("error", install_result.reason)
