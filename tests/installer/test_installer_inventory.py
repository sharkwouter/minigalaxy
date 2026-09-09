import json
import os
import shutil

from unittest import TestCase

from minigalaxy import Platform
from minigalaxy.file_info import FileInfo
from minigalaxy.game import Game
from minigalaxy.installer import InstallerInventory


def prepare_inventory(installer_name, md5, size) -> InstallerInventory:
    """Helper tool to construct instances of InstallerInventory for tests.
    Takes data for a single file.
    """
    inventory = InstallerInventory(installer_name)
    inventory.add_file(installer_name, FileInfo(md5, size))
    return inventory


class TestInventory(TestCase):

    def setUp(self):
        md5_sum = "5cc68247b61ba31e37e842fd04409d98"
        installer_name = "beneath_a_steel_sky_en_gog_2_20150.sh"
        self.test_dir = f"/tmp/minigalaxy-test/{id(self)}"
        self.game = Game("Beneath A Steel Sky", game_id=20150, install_dir="/home/makson/GOG Games/Beneath a Steel Sky")
        self.installer_path = f"{self.test_dir}/download/Beneath a Steel Sky/{installer_name}"
        self.inventory = prepare_inventory(self.installer_path, md5_sum, 0)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        super().tearDown()

    def test_as_keep_files_list_include_json(self):
        inventory_files = self.inventory.as_keep_files_list()
        json_file_name = self.installer_path.replace('.sh', '.json')

        self.assertEqual(2, len(inventory_files))
        self.assertIn(json_file_name, inventory_files)

    def test_load_save(self):
        self.inventory.item_id = self.game.id
        self.inventory.target_platform = Platform.LINUX
        self.inventory.save()

        expected_json = {
            "beneath_a_steel_sky_en_gog_2_20150.sh": {
                "size": 0,
                "md5": "5cc68247b61ba31e37e842fd04409d98"
            },
            "%META%": {
                "gogid": 20150,
                "platform": Platform.LINUX.value
            }
        }

        with open(self.inventory.inventory_file, 'r') as raw_json_file:
            raw_json = json.load(raw_json_file)

        self.assertEqual(expected_json, raw_json)

        loaded_inventory = InstallerInventory.from_file_system(self.inventory.inventory_file)
        self.assertEqual(self.inventory, loaded_inventory)
