import os
import json
from minigalaxy.paths import CONFIG_DIR, CONFIG_FILE_PATH, DEFAULT_INSTALL_DIR

DEFAULT_CONFIG = {
            "lang": "en",
            "install_dir": DEFAULT_INSTALL_DIR,
            "keep_installers": False,
            "stay_logged_in": True
        }


class Config:
    def __init__(self):
        self.__config_file = CONFIG_FILE_PATH
        self.__config = self.__load_config_file()

    def __load_config_file(self) -> dict:
        if os.path.exists(self.__config_file):
            with open(self.__config_file, "r") as file:
                return json.loads(file.read())
        else:
            return self.__create_config_file()

    def __create_config_file(self) -> dict:
        # Make sure the configuration directory exists before creating the configuration file
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(self.__config_file, "w") as file:
            file.write(json.dumps(DEFAULT_CONFIG))
            file.close()

        # Make sure the default installation path exists
        if not os.path.isdir(DEFAULT_INSTALL_DIR):
            os.makedirs(DEFAULT_INSTALL_DIR)

        return DEFAULT_CONFIG

    def __update_config_file(self):
        with open(self.__config_file, "w") as file:
            file.write(json.dumps(self.__config))
            file.close()

    def set(self, key, value):
        self.__config[key] = value
        self.__update_config_file()

    @staticmethod
    def get(key):
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, "r") as file:
                config = json.loads(file.read())
                try:
                    return config[key]
                except KeyError:
                    pass
        return None

    def unset(self, key):
        try:
            del self.__config[key]
            self.__update_config_file()
            return True
        except:
            return False
