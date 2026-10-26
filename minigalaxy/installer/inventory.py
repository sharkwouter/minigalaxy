import json
import os

from enum import StrEnum

from minigalaxy import Platform
from minigalaxy.file_info import FileInfo
from minigalaxy.file_utils import safe_delete


class InstallerInventory:
    '''Helper class to keep track of completeness of installer downloads'''

    class MetaKey(StrEnum):
        """Lists and contains all meta data keys used by InstallerInventory"""

        ID = "gogid"
        PLATFORM = "platform"
        EXECUTABLE = "exe"

    def __init__(self, installer_path=None):
        self.inventory_file = None
        self.data = {}
        self.meta = {}
        if installer_path:
            self.set_path_once(installer_path)

    @staticmethod
    def from_file_system(installer_executable_path, files_to_check: list[str] | None = None):
        """
        Helper utility to build an instance of InstallerInventory from files in the same directory
        as the file given with 'installer_executable_path'.
        Expects the following naming convention:
        - game_installer_version.[exe|sh]
        - game_installer_version-1.bin
        - game_installer_version-2.bin ...

        The inventory will contain all files names matching the base name of the installer (without extension).
        Only files in the SAME directory are checked. No recursion.
        The directory can contain multiple inventories with different names for several versions,
        but result and behaviour are unspecified for mixed platform directories.

        This is a fallback for games that have been downloaded before InstallerInventory was introduced.
        Files added like this won't have checksums and the is_complete check makes little sense.

        @param files_to_check: optional. Used as a performance optimization in situations where a directory is
               iterated by the calling code as well.
        """
        inventory = InstallerInventory(installer_executable_path)
        if os.path.isfile(inventory.inventory_file):
            return inventory

        # if the file doesn't exist, populate from disk to get names at the very least
        directory_content = files_to_check if files_to_check else os.listdir(inventory.directory)
        for f in directory_content:
            fullpath = os.path.join(inventory.directory, f)
            if os.path.isfile(fullpath) and f.startswith(inventory.name_prefix):
                inventory.add_file(f, FileInfo(size=InstallerInventory.size_of(fullpath)))

        return inventory

    @staticmethod
    def size_of(file):
        return os.stat(file).st_size

    @property
    def installer_executable(self) -> str | None:
        if not self.meta.get(InstallerInventory.MetaKey.EXECUTABLE, None):
            executable = self.__search_executable()
            if executable:
                self.meta[InstallerInventory.MetaKey.EXECUTABLE] = executable
        return self.meta.get(InstallerInventory.MetaKey.EXECUTABLE, None)

    @installer_executable.setter
    def installer_executable(self, new_value: str) -> None:
        self.meta[InstallerInventory.MetaKey.EXECUTABLE] = new_value

    @property
    def item_id(self):
        return self.meta.get(InstallerInventory.MetaKey.ID, 0)

    @item_id.setter
    def item_id(self, new_value) -> None:
        self.meta[InstallerInventory.MetaKey.ID] = new_value

    @property
    def target_platform(self):
        if not self.meta.get(InstallerInventory.MetaKey.PLATFORM, None):
            platform = self.__detect_platform_type()
            self.meta[InstallerInventory.MetaKey.PLATFORM] = platform
        return self.meta[InstallerInventory.MetaKey.PLATFORM]

    @target_platform.setter
    def target_platform(self, new_value: str) -> None:
        self.meta[InstallerInventory.MetaKey.PLATFORM] = new_value

    def set_path_once(self, installer_path=None):
        """Encapsulates a batch of one-time initialisations like setting directory and inventory file names.
        The initialisation also tries to directly load the contents of the inventory file via `load` (if existing).
        This only happens when the name of the inventory file wasn't created yet AND a none-empty path was given.
        Without a path, the function only tries to deduce a few (new) meta data items from the inventory's file list.
        """
        if not self.inventory_file and installer_path:
            self.directory = os.path.dirname(installer_path)
            self.name_prefix = os.path.basename(os.path.splitext(installer_path)[0])
            self.inventory_file = os.path.join(self.directory, f"{self.name_prefix}.json")
            self.load()

        # some code to handle old installer inventories and pre-inventory downloaded files
        # These are only relevant when path doesn't point to a json, but is a sh or exe.
        # When it's a json, it should contain a none-empty file list which the regular getters can handle
        # because saving an empty inventory doesn't make sense at all
        if self.contained_files():
            return
        if not self.target_platform:
            # try to init target_platform from the installer path alone if the inventory doesn't have a file list
            self.target_platform = self.__detect_platform_type([installer_path])
        if not self.installer_executable:
            self.installer_executable = self.__search_executable([installer_path])

    def load(self):
        """Try to read the inventory from file. This function applies a rudimentary merge between meta data from file
        and any key which might already exist on the instance.
        Values set on the instance will take priority over data from the file.

        This is mostly required for situations where an instance of `InstallerInventory` is (re-)created before the full
        path to the executable is known (e.g. when creating a new inventory in download preparation before looping files).
        In that case, `load_path_once` must be called later and there is the danger of adding metadata BEFORE `load`
        is called. This metadata would be lost once the initialisation is done, leading to very hard to find bugs with
        data consistency.

        The underlying assumption is that inventory files age, and code will include migration logic when rewriting them.
        """
        if not os.path.isfile(self.inventory_file):
            return self.data

        with open(self.inventory_file, 'r') as inventory:
            self.data = json.load(inventory)

        new_meta = self.data.get('%META%', {})
        if new_meta:
            enum_members = [*InstallerInventory.MetaKey]
            for key in new_meta:
                # drop obsolete keys by not picking them up from the file
                if key not in enum_members:
                    continue
                self.meta.setdefault(key, new_meta[key])

        if "%META%" in self.data:
            del self.data['%META%']

        return self.data

    def save(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory, mode=0o755)

        with open(self.inventory_file, 'w') as inventory_file:
            payload = self.data.copy()
            payload['%META%'] = self.meta.copy()
            json.dump(payload, inventory_file, indent=2)

    def add_file(self, name: str, file_info: FileInfo):
        self.data[os.path.basename(name)] = file_info.as_dict()
        if self.meta.get(InstallerInventory.MetaKey.EXECUTABLE, None):
            return
        executable = self.__search_executable(files=[name])
        if executable:
            self.meta[InstallerInventory.MetaKey.EXECUTABLE] = executable

    def has_checksum(self, file_name):
        return not self.data.get(file_name, {}).get("md5", None) is None

    def verify_checksum(self, file_name, actual_checksum):
        file_info = self.data.get(file_name)
        recorded_checksum = file_info.get("md5", "")
        if recorded_checksum == actual_checksum:
            return True
        else:
            file_info["md5"] = False
            return False

    def get_expected_total_size(self):
        total_size = 0
        for file_data in self.data.values():
            total_size += file_data.get('size', 0)
        return total_size

    def is_complete(self):
        self.load()
        if not self.data:
            return False

        for file in self.data.keys():
            full_path = os.path.join(self.directory, file)
            if not os.path.exists(full_path) or InstallerInventory.size_of(full_path) != self.data[file].get("size", 0):
                return False

        return True

    def as_keep_files_list(self):
        """Returns a list of all files contained in this inventory INCLUDING the inventory itself"""
        files = self.contained_files()
        files.append(self.inventory_file)
        return files

    def contained_files(self):
        files = []
        for f in self.data.keys():
            files.append(os.path.join(self.directory, f))
        return files

    def delete_files(self):
        """delete files which are part of this inventory"""
        file_list = self.as_keep_files_list()
        file_list.append(self.directory)
        safe_delete(file_list)

    def delete_others(self):
        """
        Delete files in the same directory, which are NOT part of this inventory.
        Used to remove previous versions after successful install.
        """
        delete_list = []
        for f in os.listdir(self.directory):
            if os.path.isdir(f):
                continue
            if f not in self.data:
                delete_list.append(f)

        safe_delete(delete_list)

    def delete_invalid_files(self):
        """
        Delete files of this inventory which are flagged as having an invalid checksum.
        Flagging must have happened by calling IntallerInventory.verify_checksum.
        It is advised not to call save() afterwards because that will overwrite the recorded checksums with False
        """
        delete_list = []
        for file, info in self.data.items():
            if info.get("md5", None) is False:
                delete_list.append(os.path.join(self.directory, file))

        safe_delete(delete_list)

    def __detect_platform_type(self, files=[]):
        """Go over the list of files in the installer and determine OS based on file name endings.
        @param files: optional. Uses the files contained in the installer by default.
               Can be used in situations where the installer itself doesn't contain any files (yet)
        """
        if not files:
            files = self.contained_files()
        if list(filter(lambda n: n.endswith(".sh"), files)):
            return Platform.LINUX
        if list(filter(lambda n: n.endswith(".exe") or n.endswith(".bin"), files)):
            return Platform.WINDOWS

        return None

    def __search_executable(self, files=[]):
        """Search the actual installer executable in the list of inventory files.
        @param files: optional. Uses the files contained in the installer by default.
               Can be used in situations where the installer itself doesn't contain any files (yet).
        """
        if not files:
            files = self.contained_files()
        if len(files) == 1:
            return files[0]  # small performance improvement for sh installers
        for f in files:
            if f.endswith(".exe") or f.endswith(".sh"):
                return f
        return None

    def __str__(self):
        return f"InstallerInventory(id={self.item_id}, plf={self.target_platform}, exe={self.installer_executable})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, InstallerInventory):
            return False
        return self.data == other.data and self.meta == other.meta
