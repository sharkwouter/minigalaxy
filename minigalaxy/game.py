import re


class Game:
    def __init__(self, name: str, game_id: int = 0, image_url: str = "", install_dir: str = ""):
        self.name = name
        self.id = game_id
        self.image_url = image_url
        self.image_path = self.__get_image_path()
        self.install_dir = install_dir

    def __get_image_path(self) -> str:
        return ""

    def __eq__(self, other):
        if self.id and other.id and self.id == other.id:
            return True
        if self.name == other.name:
            return True
        # Compare names with special characters and capital letters removed
        name1_cleaned = re.sub('[^A-Za-z0-9]+', '', self.name).lower()
        name2_cleaned = re.sub('[^A-Za-z0-9]+', '', other.name).lower()
        if name1_cleaned == name2_cleaned:
            return True

        return False

    def __str__(self):
        return self.name
