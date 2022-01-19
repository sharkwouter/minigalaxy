import os
import threading
import json
import time
from minigalaxy.paths import CONFIG_DIR, CONFIG_FILE_PATH, DEFAULT_INSTALL_DIR

# The default values for new configuration files
DEFAULT_CONFIGURATION = {
    "locale": "",
    "lang": "en",
    "view": "grid",
    "install_dir": DEFAULT_INSTALL_DIR,
    "keep_installers": False,
    "stay_logged_in": True,
    "use_dark_theme": False,
    "show_hidden_games": False,
    "show_windows_games": False,
    "keep_window_maximized": False,
    "installed_filter": False,
    "create_applications_file": False
}


# Make sure you never spawn two instances of this class
# If multiple instances go out of sync, they will overwrite each others changes
# The config file is only read once upon starting up
class __Config:
    def __init__(self):
        self.first_run = False
        self.__config = {}
        self.__config_file = CONFIG_FILE_PATH
        self.__update_required = False

    def first_run_init(self):
        if not self.first_run:
            self.first_run = True
            self.__config = self.__load_config_file()
            self.__add_missing_config_entries()
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
                try:
                    return json.loads(file.read())
                except json.decoder.JSONDecodeError:
                    print("Reading config.json failed, creating new config file.")
                    return self.__create_config_file()
        else:
            return self.__create_config_file()

    def __create_config_file(self) -> dict:
        # Make sure the configuration directory exists before creating the configuration file
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, mode=0o755)
        with open(self.__config_file, "w") as file:
            file.write(json.dumps(DEFAULT_CONFIGURATION))
            file.close()

        # Make sure the default installation path exists
        if not os.path.isdir(DEFAULT_CONFIGURATION['install_dir']):
            os.makedirs(DEFAULT_CONFIGURATION['install_dir'], mode=0o755)

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
        self.first_run_init()
        self.__config[key] = value
        self.__update_required = True

    def get(self, key):
        self.first_run_init()
        try:
            return self.__config[key]
        except KeyError:
            return None

    def unset(self, key):
        self.first_run_init()
        try:
            del self.__config[key]
            self.__update_required = True
        except KeyError:
            pass


Config = __Config()
