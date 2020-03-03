import os
import threading
import json
import time
from minigalaxy.paths import CONFIG_DIR, CONFIG_FILE_PATH
from minigalaxy.constants import DEFAULT_CONFIGURATION


# Make sure you never spawn two instances of this class
# If multiple instances go out of sync, they will overwrite each others changes
# The config file is only read once upon starting up
class __Config:
    def __init__(self):
        self.__config_file = CONFIG_FILE_PATH
        self.__config = self.__load_config_file()
        self.__add_missing_config_entries()
        self.__update_required = False

        # Update the config file regularly to reflect the self.__config dictionary
        keep_config_synced_thread = threading.Thread(target=self.__keep_config_synced)
        keep_config_synced_thread.daemon = True
        keep_config_synced_thread.start()

    def __keep_config_synced(self):
        while True:
            if self.__update_required:
                self.__update_config_file()
                self.__update_required = False
            time.sleep(0.1)

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
            file.write(json.dumps(DEFAULT_CONFIGURATION))
            file.close()

        # Make sure the default installation path exists
        if not os.path.isdir(DEFAULT_CONFIGURATION['install_dir']):
            os.makedirs(DEFAULT_CONFIGURATION['install_dir'])

        return DEFAULT_CONFIGURATION

    def __update_config_file(self):
        with open(self.__config_file, "w") as file:
            file.write(json.dumps(self.__config))
            file.close()

    def __add_missing_config_entries(self):
        # Make sure all config values in the default configuration are available
        added_value = False
        for key in DEFAULT_CONFIGURATION:
            if self.get(key) is None:
                self.set(key, DEFAULT_CONFIGURATION[key])
                added_value = True
        if added_value:
            self.__update_config_file()
            self.__config = self.__load_config_file()

    def set(self, key, value):
        self.__config[key] = value
        self.__update_required = True

    def get(self, key):
        try:
            return self.__config[key]
        except KeyError:
            return None

    def unset(self, key):
        try:
            del self.__config[key]
            self.__update_required = True
        except:
            pass


Config = __Config()
