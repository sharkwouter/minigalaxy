import os
import re
import pickle


class Game:
    def __init__(self, name: str, url: str = "", game_id: int = 0, install_dir: str = "", image_url="",
                 platform="linux", dlcs=[]):
        self.name = name
        self.url = url
        self.id = game_id
        self.install_dir = install_dir
        self.image_url = image_url
        self.platform = platform
        self.installed_version = self.get_installed_version()
        self.dlcs = dlcs

    def get_stripped_name(self):
        return self.__strip_string(self.name)

    def get_install_directory_name(self):
        return re.sub('[^A-Za-z0-9 ]+', '', self.name)

    @staticmethod
    def __strip_string(string):
        return re.sub('[^A-Za-z0-9]+', '', string)

    def get_installed_version(self):
        gameinfo = os.path.join(self.install_dir, "gameinfo")
        gameinfo_list = []
        if os.path.isfile(gameinfo):
            with open(gameinfo, 'r') as file:
                gameinfo_list = file.readlines()
        if len(gameinfo_list) > 1:
            version = gameinfo_list[1].strip()
        else:
            version = ""
        return version

    def validate_if_installed_is_latest(self, installers):
        if not self.installed_version:
            is_latest = False
        else:
            current_installer = None
            for installer in installers:
                if installer["os"] == self.platform:
                    current_installer = installer
                    break
            if current_installer is not None and current_installer["version"] == self.installed_version:
                is_latest = False
            else:
                is_latest = True
        return is_latest

    def get_dlc_status(self, dlc_title):
        status_list = ["installed", "updatable", "not-installed", "not-installable"]
        status = status_list[2]
        dlc_status_file_name = "minigalaxy-dlc.pickle"
        dlc_status_file_path = os.path.join(self.install_dir, dlc_status_file_name)
        if self.installed_version:
            if os.path.isfile(dlc_status_file_path):
                dlc_staus_file = open(dlc_status_file_path, 'rb')
                dlc_status_dict = pickle.load(dlc_staus_file)
                dlc_staus_file.close()
                if dlc_status_dict[dlc_title]:
                    status = status_list[0]
        return status

    def set_dlc_status(self, dlc_title, status):
        dlc_status_file_name = "minigalaxy-dlc.pickle"
        dlc_status_file_path = os.path.join(self.install_dir, dlc_status_file_name)
        if self.installed_version:
            if os.path.isfile(dlc_status_file_path):
                dlc_staus_file = open(dlc_status_file_path, 'rb')
                dlc_status_dict = pickle.load(dlc_staus_file)
                dlc_staus_file.close()
            else:
                dlc_status_dict = {}
            for dlc in self.dlcs:
                if dlc["title"] not in dlc_status_dict:
                    dlc_status_dict[dlc["title"]] = False
            dlc_status_dict[dlc_title] = status
            dlc_staus_file = open(dlc_status_file_path, 'wb')
            pickle.dump(dlc_status_dict, dlc_staus_file)
            dlc_staus_file.close()

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if self.id > 0 and other.id > 0:
            if self.id == other.id:
                return True
            else:
                return False
        if self.name == other.name:
            return True
        # Compare names with special characters and capital letters removed
        if self.get_stripped_name().lower() == other.get_stripped_name().lower():
            return True
        if self.install_dir and other.get_stripped_name() in self.__strip_string(self.install_dir):
            return True
        if other.install_dir and self.get_stripped_name() in self.__strip_string(other.install_dir):
            return True
        return False

    def __lt__(self, other):
        names = [str(self), str(other)]
        names.sort()
        if names[0] == str(self):
            return True
        return False
