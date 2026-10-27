import time

from unittest import TestCase, mock
from unittest.mock import MagicMock
from threading import RLock, Thread

from minigalaxy.installer import core as installer

from minigalaxy import Platform
from minigalaxy.config import Config
from minigalaxy.file_info import FileInfo
from minigalaxy.game import Game
from minigalaxy.installer import InstallerInventory, InstallTask


class TestInstallQueue(TestCase):

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
            self.assertTrue(test_queue.is_empty(), "Queue should be empty again")
            self.assertFalse(spawned_worker.is_alive(), "Worker thread should be dead when the queue is empty")
            self.assertIsNone(test_queue.worker, "Worker thread should be gone")
        finally:
            test_queue.queue.clear()
            lock.release()

    @mock.patch('minigalaxy.installer.core.InstallerQueue')
    def test_enqueue_game_install_lazy_init(self, mock_queue_class):
        '''[scenario: The very first invocation of installer.enqueue_game_install creates the global InstallerQueue]'''

        installer.INSTALL_QUEUE = None

        queue_instance = MagicMock()
        mock_queue_class.return_value = queue_instance

        self.assertIsNone(installer.INSTALL_QUEUE, "Global INSTALL_QUEUE must not exist yet")
        game = Game("Beneath A Steel Sky", install_dir="/home/makson/GOG Games/Beneath a Steel Sky")
        inventory = InstallerInventory()
        inventory.item_id = 42
        installer.enqueue_game_install(MagicMock(), game, inventory)

        self.assertIs(queue_instance, installer.INSTALL_QUEUE)
        queue_instance.put.assert_called_once()

    @mock.patch('minigalaxy.installer.core.install_game')
    def test_enqueue_game(self, mock_install):
        """[scenario: Game gets queued and ultimately runs into install_game]"""

        installer.INSTALL_QUEUE = None
        result_callback = MagicMock()
        config = MagicMock()

        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform=Platform.WINDOWS)
        inventory = InstallerInventory("adrift.exe")
        inventory.item_id = 12345
        installer.enqueue_game_install(result_callback,
                                       game, inventory=inventory, config=config)
        time.sleep(0.5)
        lock = installer.INSTALL_QUEUE.state_lock
        with lock:
            mock_install.assert_called_once()
            result_callback.assert_called_once_with(installer.InstallResult(
                12345, installer.InstallResultType.SUCCESS, "/home/makson/GOG Games/Absolute Drift"
            ))

    @mock.patch('minigalaxy.installer.core.install_game')
    def test_enqueue_game_failure(self, mock_install):
        """[scenario: Game gets queued and ultimately runs into install_game]"""

        installer.INSTALL_QUEUE = None
        result_callback = MagicMock()
        mock_install.side_effect = installer.InstallException("error")

        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform=Platform.WINDOWS)
        inventory = InstallerInventory()
        inventory.item_id = 12345
        installer.enqueue_game_install(result_callback,
                                       game, inventory, config=Config())
        time.sleep(0.5)
        lock = installer.INSTALL_QUEUE.state_lock
        with lock:
            mock_install.assert_called_once()
            result_callback.assert_called_once_with(installer.InstallResult(
                12345, installer.InstallResultType.FAILURE, "error"
            ))

    def test_InstallTask_init_requires_callback(self):
        '''[scenario: InstallTask__init__ enforces result_callback to be a callable]'''

        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform=Platform.WINDOWS)
        inventory = InstallerInventory("/not/a/real/installer.exe")
        inventory.item_id = 815
        with self.assertRaises(ValueError) as cm:
            installer.InstallTask("not-a-callable", game, inventory=inventory)
        # the search for a Game instance happens before the check of callback, so assert the message as well
        self.assertEqual("result_callback is required", str(cm.exception))

    def test_InstallTask_init_requires_Game(self):
        '''[scenario: InstallTask__init__ must have received a Game instance as part of *args or **kwargs]'''

        def callback(): pass

        game = Game("Absolute Drift", install_dir="/home/makson/GOG Games/Absolute Drift", platform=Platform.WINDOWS)
        inventory = InstallerInventory("/not/a/real/installer.exe")
        inventory.item_id = 815

        with self.assertRaises(ValueError) as cm:
            installer.InstallTask(callback, inventory=inventory)
        self.assertEqual("No instance of Game in InstallTask constructor arguments", str(cm.exception))

        # counter-test: pass game as part of kwargs, it should not raise an exception
        installer.InstallTask(callback, game=game, inventory=inventory)

    def test_locate_argument_byType(self):
        test_args = [self, Config()]
        test_kwargs = {
            "callable": MagicMock(),
            "file_info": FileInfo("", 0)
        }

        self.assertIs(test_args[1], InstallTask._locate_type_in_args(Config, *test_args, **test_kwargs))
        self.assertIs(test_kwargs["callable"], InstallTask._locate_type_in_args(MagicMock, *test_args, **test_kwargs))

    def test_locate_argument_byType_fails(self):
        test_args = [self, Config()]
        test_kwargs = {
            "callable": MagicMock(),
            "file_info": FileInfo("", 0)
        }

        with self.assertRaises(ValueError) as error:
            InstallTask._locate_type_in_args(Game, *test_args, **test_kwargs)

        self.assertEqual("No instance of Game in InstallTask constructor arguments", str(error.exception))
