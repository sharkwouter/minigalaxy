import os
import re
from minigalaxy.paths import THUMBNAIL_DIR


class Game:
    def __init__(self, name: str, game_id: int = 0, install_dir: str = "", image_url=""):
        self.name = name
        self.id = game_id
        self.install_dir = install_dir

    def get_image_path(self) -> str:
        return os.path.join(THUMBNAIL_DIR, "{}.png".format(self.get_stripped_name()))

    def get_stripped_name(self):
        return self.__strip_string(self.name)

    def __strip_string(self, string):
        return re.sub('[^A-Za-z0-9]+', '', string)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if self.id and other.id and self.id == other.id:
            return True
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
