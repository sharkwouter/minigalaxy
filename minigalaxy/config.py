import os
import json
from minigalaxy.directories import CONFIG_DIR, DEFAULT_INSTALL_DIR

DEFAULT_CONFIG = {
            "lang": "en",
            "install_dir": DEFAULT_INSTALL_DIR,
            "keep_installers": False
        }


class Config:
    def __init__(self):
        self.__config_file = os.path.join(CONFIG_DIR, "config.json")
        self.__config = self.__load_config_file()

    def __load_config_file(self) -> dict:
        if os.path.exists(self.__config_file):
            with open(self.__config_file, "r") as file:
                return json.loads(file.read())
        else:
            return self.__create_config_file()

    def __create_config_file(self) -> dict:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(self.__config_file, "w") as file:
            file.write(json.dumps(DEFAULT_CONFIG))
            file.close()
        return DEFAULT_CONFIG

    def __update_config_file(self):
        with open(self.__config_file, "w") as file:
            file.write(json.dumps(self.__config))
            file.close()

    def set(self, key, value):
        self.__config[key] = value
        self.__update_config_file()

    def get(self, key):
        try:
            return self.__config[key]
        except KeyError:
            return None
