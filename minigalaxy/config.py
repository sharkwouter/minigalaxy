import os
import json

from minigalaxy.logger import logger
from minigalaxy.paths import CONFIG_FILE_PATH, DEFAULT_INSTALL_DIR

# Moved from constants.py to here because of circular import between translations, config and constants
# UI download threads are for UI assets like thumbnails or icons
UI_DOWNLOAD_THREADS = 4
# Game download threads are for long-running downloads like games, DLC or updates
DEFAULT_DOWNLOAD_THREAD_COUNT = 4


class Config:

    __config_file: str
    __config: dict

    def __init__(self, config_file: str = CONFIG_FILE_PATH):
        self.__is_batch_edit = False
        self.__config_file = config_file
        self.__config = {}
        self.__load()

    def __load(self) -> None:
        if os.path.isfile(self.__config_file):
            with open(self.__config_file, "r", encoding="utf-8") as file:
                try:
                    self.__config = json.loads(file.read())
                except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                    logger.warning("Reading config.json failed, creating new config file.")
                    os.remove(self.__config_file)

    def __write(self) -> None:
        if not os.path.isfile(self.__config_file):
            config_dir = os.path.dirname(self.__config_file)
            os.makedirs(config_dir, mode=0o700, exist_ok=True)
        temp_file = f"{self.__config_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            file.write(json.dumps(self.__config, ensure_ascii=False))
        os.rename(temp_file, self.__config_file)

    def start_batch_edit(self):
        """
        Flags config for multiple incoming changes. Normally, every change is written to file immediately.
        This can lead to a lot redundant writes when several settings are changed in quick succession.
        This method provides a uniform way to flag Config in a rudimentary type of 'transaction'.
        Any setter which internally uses '__set_and_write' will honor this flag.
        Use 'Config.save()' to finalize (remove flag and write to the file to disc).
        """
        self.__is_batch_edit = True

    def cancel_batch_edit(self):
        """
        The counterpart to 'Config.start_batch_edit()'.
        Resets the flag and reverts all changes since the last write/save.
        """
        self.__is_batch_edit = False
        self.__load()

    def save(self) -> None:
        """
        Config will normally immediately save all changes applied to it to the configuration file automatically.
        This mechanism relies on getters and setters and the method `config.__write` is called whenever
        one of the properties is assigned a new value.
        So it only works for direct assignments. But there are some properties which returned Lists or might
        return other none-simple types in the future. Changes made to these sub-objects would not be detected
        and thus also not be persisted automatically.
        In these situations `Config.save()`  can be used to avoid having to re-assign the same object reference.
        This method is also needed when editing Config in 'batch mode' to finalize the state.
        """
        self.__write()
        self.__is_batch_edit = False

    def __set_and_write(self, property_name, new_value):
        if self.__config.get(property_name, None) == new_value:
            return

        if new_value is None:
            del self.__config[property_name]
            logger.warning("Config setting '%' was deleted (=reset to default)")
        else:
            self.__config[property_name] = new_value

        if not self.__is_batch_edit:
            self.__write()

    @property
    def locale(self) -> str:
        return self.__config.get("locale", "")

    @locale.setter
    def locale(self, new_value: str) -> None:
        self.__set_and_write("locale", new_value)

    @property
    def lang(self) -> str:
        return self.__config.get("lang", "en")

    @lang.setter
    def lang(self, new_value: str) -> None:
        self.__set_and_write("lang", new_value)

    @property
    def view(self) -> str:
        return self.__config.get("view", "grid")

    @view.setter
    def view(self, new_value: str) -> None:
        self.__set_and_write("view", new_value)

    @property
    def install_dir(self) -> str:
        return self.__config.get("install_dir", DEFAULT_INSTALL_DIR)

    @install_dir.setter
    def install_dir(self, new_value: str) -> None:
        self.__set_and_write("install_dir", new_value)

    @property
    def username(self) -> str:
        return self.__config.get("username", "")

    @username.setter
    def username(self, new_value: str) -> None:
        self.__set_and_write("username", new_value)

    @property
    def refresh_token(self) -> str:
        return self.__config.get("refresh_token", "")

    @refresh_token.setter
    def refresh_token(self, new_value: str) -> None:
        self.__set_and_write("refresh_token", new_value)

    @property
    def keep_installers(self) -> bool:
        return self.__config.get("keep_installers", False)

    @keep_installers.setter
    def keep_installers(self, new_value: bool) -> None:
        self.__set_and_write("keep_installers", new_value)

    @property
    def stay_logged_in(self) -> bool:
        return self.__config.get("stay_logged_in", True)

    @stay_logged_in.setter
    def stay_logged_in(self, new_value: bool) -> None:
        self.__set_and_write("stay_logged_in", new_value)

    @property
    def use_dark_theme(self) -> bool:
        return self.__config.get("use_dark_theme", False)

    @use_dark_theme.setter
    def use_dark_theme(self, new_value: bool) -> None:
        self.__set_and_write("use_dark_theme", new_value)

    @property
    def show_hidden_games(self) -> bool:
        return self.__config.get("show_hidden_games", False)

    @show_hidden_games.setter
    def show_hidden_games(self, new_value: bool) -> None:
        self.__set_and_write("show_hidden_games", new_value)

    @property
    def show_windows_games(self) -> bool:
        return self.__config.get("show_windows_games", False)

    @show_windows_games.setter
    def show_windows_games(self, new_value: bool) -> None:
        self.__set_and_write("show_windows_games", new_value)

    @property
    def keep_window_maximized(self) -> bool:
        return self.__config.get("keep_window_maximized", False)

    @keep_window_maximized.setter
    def keep_window_maximized(self, new_value: bool) -> None:
        self.__set_and_write("keep_window_maximized", new_value)

    @property
    def installed_filter(self) -> bool:
        return self.__config.get("installed_filter", False)

    @installed_filter.setter
    def installed_filter(self, new_value: bool) -> None:
        self.__set_and_write("installed_filter", new_value)

    @property
    def create_applications_file(self) -> bool:
        return self.__config.get("create_applications_file", False)

    @create_applications_file.setter
    def create_applications_file(self, new_value: bool) -> None:
        self.__set_and_write("create_applications_file", new_value)

    @property
    def max_parallel_game_downloads(self) -> int:
        return self.__config.get("max_download_workers", DEFAULT_DOWNLOAD_THREAD_COUNT)

    @max_parallel_game_downloads.setter
    def max_parallel_game_downloads(self, new_value: int) -> None:
        self.__set_and_write("max_download_workers", new_value)

    @property
    def current_downloads(self) -> list:
        """
        Returns a list of game ids which are currently being downloaded.
        The list is a shallow copy of the internal representation to guard Config against changes by side-effects.
        """
        return [*self.__config.get("current_downloads", [])]

    @current_downloads.setter
    def current_downloads(self, new_value: list) -> None:
        self.__set_and_write("current_downloads", new_value)

    def add_ongoing_download(self, download_id):
        '''Adds the given id to the list of active downloads if not contained already. Does nothing otherwise.'''
        current = self.current_downloads
        if download_id not in current:
            current.append(download_id)
            self.current_downloads = current

    def remove_ongoing_download(self, download_id):
        '''Removes the given id from the list of active downloads, if contained. Does nothing otherwise.'''
        current = self.current_downloads
        if download_id in current:
            current.remove(download_id)
            self.current_downloads = current

    @property
    def paused_downloads(self) -> dict:
        """
        Returns a dict of 'filename:progress_percent' of files which are currently being downloaded.
        The ldict is a shallow copy of the internal representation to guard Config against changes by side-effects.
        """
        return {**self.__config.get("paused_downloads", {})}

    @paused_downloads.setter
    def paused_downloads(self, new_value: dict) -> None:
        """Ongoing downloads are a dictionary of filename:progress_percentage_int. See Download.current_progress."""
        self.__set_and_write("paused_downloads", new_value)

    def add_paused_download(self, save_location, current_progress):
        paused = self.paused_downloads
        paused[save_location] = current_progress
        self.paused_downloads = paused

    def remove_paused_download(self, save_location):
        paused = self.paused_downloads
        if save_location in paused:
            del paused[save_location]
            self.paused_downloads = paused
