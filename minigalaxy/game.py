import os
import re
import json


class Game:
    def __init__(self, name: str, url: str = "", game_id: int = 0, install_dir: str = "", image_url="",
                 platform="linux", dlcs=None):
        self.name = name
        self.url = url
        self.id = game_id
        self.install_dir = install_dir
        self.image_url = image_url
        self.platform = platform
        self.installed_version = ""
        if dlcs is None:
            dlcs = []
        self.dlcs = dlcs

        self.dlc_status_list = ["not-installed", "installed", "updatable"]
        self.dlc_status_file_name = "minigalaxy-dlc.json"
        self.dlc_status_file_path = ""
        self.read_installed_version()

    def get_stripped_name(self):
        return self.__strip_string(self.name)

    def get_install_directory_name(self):
        return re.sub('[^A-Za-z0-9 ]+', '', self.name)

    @staticmethod
    def __strip_string(string):
        return re.sub('[^A-Za-z0-9]+', '', string)

    def read_installed_version(self):
        gameinfo = os.path.join(self.install_dir, "gameinfo")
        gameinfo_list = []
        if os.path.isfile(gameinfo):
            with open(gameinfo, 'r') as file:
                gameinfo_list = file.readlines()
        if len(gameinfo_list) > 1:
            version = gameinfo_list[1].strip()
        else:
            version = ""
        self.installed_version = version
        self.dlc_status_file_path = os.path.join(self.install_dir, self.dlc_status_file_name)

    def validate_if_installed_is_latest(self, installers):
        self.read_installed_version()
        if not self.installed_version:
            is_latest = False
        else:
            current_installer = None
            for installer in installers:
                if installer["os"] == self.platform:
                    current_installer = installer
                    break
            if current_installer is not None and current_installer["version"] != self.installed_version:
                is_latest = False
            else:
                is_latest = True
        return is_latest

    def get_dlc_status(self, dlc_title):
        self.read_installed_version()
        status = self.dlc_status_list[0]
        if self.installed_version:
            if os.path.isfile(self.dlc_status_file_path):
                dlc_staus_file = open(self.dlc_status_file_path, 'r')
                json_list = json.load(dlc_staus_file)
                dlc_status_dict = json_list[0]
                dlc_staus_file.close()
                if dlc_title in dlc_status_dict:
                    status = dlc_status_dict[dlc_title]
                else:
                    status = self.dlc_status_list[0]
        return status

    def set_dlc_status(self, dlc_title, status):
        self.read_installed_version()
        if self.installed_version:
            if os.path.isfile(self.dlc_status_file_path):
                dlc_staus_file = open(self.dlc_status_file_path, 'r')
                json_list = json.load(dlc_staus_file)
                dlc_status_dict = json_list[0]
                dlc_installers_version_dict = json_list[1]
                dlc_staus_file.close()
            else:
                dlc_status_dict = {}
                dlc_installers_version_dict = {}
            for dlc in self.dlcs:
                if dlc["title"] not in dlc_status_dict:
                    dlc_status_dict[dlc["title"]] = self.dlc_status_list[0]
            if status:
                dlc_status_dict[dlc_title] = self.dlc_status_list[1]
                dlc_installers = {}
                for dlc in self.dlcs:
                    if dlc_title == dlc["title"]:
                        dlc_installers = dlc["downloads"]["installers"]
                dlc_installers_version_dict[dlc_title] = dlc_installers
            else:
                dlc_status_dict[dlc_title] = self.dlc_status_list[0]
            dlc_status_file = open(self.dlc_status_file_path, 'w')
            json.dump([dlc_status_dict, dlc_installers_version_dict], dlc_status_file)
            dlc_status_file.close()

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
