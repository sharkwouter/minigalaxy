import os
import json
from typing import List

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

    def save(self) -> None:
        """
        Config will normally immediately save all changes applied to it to the configuration file automatically.
        This mechanism relies on getters and setters and the method `config.__write` is called whenever
        one of the properties is assigned a new value.
        So it only works for direct assignments. But there are some properties which returned Lists or might
        return other none-simple types in the future. Changes made to these sub-objects would not be detected
        and thus also not be persisted automatically.
        In these situations `Config.save`  can be used to avoid having to re-assign the same object reference.
        """
        self.__write()

    @property
    def locale(self) -> str:
        return self.__config.get("locale", "")

    @locale.setter
    def locale(self, new_value: str) -> None:
        self.__config["locale"] = new_value
        self.__write()

    @property
    def lang(self) -> str:
        return self.__config.get("lang", "en")

    @lang.setter
    def lang(self, new_value: str) -> None:
        self.__config["lang"] = new_value
        self.__write()

    @property
    def view(self) -> str:
        return self.__config.get("view", "grid")

    @view.setter
    def view(self, new_value: str) -> None:
        self.__config["view"] = new_value
        self.__write()

    @property
    def install_dir(self) -> str:
        return self.__config.get("install_dir", DEFAULT_INSTALL_DIR)

    @install_dir.setter
    def install_dir(self, new_value: str) -> None:
        self.__config["install_dir"] = new_value
        self.__write()

    @property
    def username(self) -> str:
        return self.__config.get("username", "")

    @username.setter
    def username(self, new_value: str) -> None:
        self.__config["username"] = new_value
        self.__write()

    @property
    def refresh_token(self) -> str:
        return self.__config.get("refresh_token", "")

    @refresh_token.setter
    def refresh_token(self, new_value: str) -> None:
        self.__config["refresh_token"] = new_value
        self.__write()

    @property
    def keep_installers(self) -> bool:
        return self.__config.get("keep_installers", False)

    @keep_installers.setter
    def keep_installers(self, new_value: bool) -> None:
        self.__config["keep_installers"] = new_value
        self.__write()

    @property
    def stay_logged_in(self) -> bool:
        return self.__config.get("stay_logged_in", True)

    @stay_logged_in.setter
    def stay_logged_in(self, new_value: bool) -> None:
        self.__config["stay_logged_in"] = new_value
        self.__write()

    @property
    def use_dark_theme(self) -> bool:
        return self.__config.get("use_dark_theme", False)

    @use_dark_theme.setter
    def use_dark_theme(self, new_value: bool) -> None:
        self.__config["use_dark_theme"] = new_value
        self.__write()

    @property
    def show_hidden_games(self) -> bool:
        return self.__config.get("show_hidden_games", False)

    @show_hidden_games.setter
    def show_hidden_games(self, new_value: bool) -> None:
        self.__config["show_hidden_games"] = new_value
        self.__write()

    @property
    def show_windows_games(self) -> bool:
        return self.__config.get("show_windows_games", False)

    @show_windows_games.setter
    def show_windows_games(self, new_value: bool) -> None:
        self.__config["show_windows_games"] = new_value
        self.__write()

    @property
    def keep_window_maximized(self) -> bool:
        return self.__config.get("keep_window_maximized", False)

    @keep_window_maximized.setter
    def keep_window_maximized(self, new_value: bool) -> None:
        self.__config["keep_window_maximized"] = new_value
        self.__write()

    @property
    def installed_filter(self) -> bool:
        return self.__config.get("installed_filter", False)

    @installed_filter.setter
    def installed_filter(self, new_value: bool) -> None:
        self.__config["installed_filter"] = new_value
        self.__write()

    @property
    def create_applications_file(self) -> bool:
        return self.__config.get("create_applications_file", False)

    @create_applications_file.setter
    def create_applications_file(self, new_value: bool) -> None:
        self.__config["create_applications_file"] = new_value
        self.__write()

    @property
    def max_parallel_game_downloads(self) -> int:
        return self.__config.get("max_download_workers", DEFAULT_DOWNLOAD_THREAD_COUNT)

    @max_parallel_game_downloads.setter
    def max_parallel_game_downloads(self, new_value: int) -> None:
        self.__config["max_download_workers"] = new_value
        self.__write()

    @property
    def current_downloads(self) -> List[int]:
        return self.__config.get("current_downloads", [])

    @current_downloads.setter
    def current_downloads(self, new_value: List[int]) -> None:
        self.__config["current_downloads"] = new_value
        self.__write()

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
    def paused_downloads(self) -> List[int]:
        return self.__config.get("paused_downloads", {})

    @paused_downloads.setter
    def paused_downloads(self, new_value: {}) -> None:
        self.__config["paused_downloads"] = new_value
        self.__write()

    def add_paused_download(self, save_location, current_progress):
        paused = self.paused_downloads
        paused[save_location] = current_progress
        self.paused_downloads = paused
        self.__write()

    def remove_paused_download(self, save_location):
        paused = self.paused_downloads
        if save_location in paused:
            del paused[save_location]
            self.paused_downloads = paused
            self.__write()

    @property
    def compatibility_layers(self) -> list:
        """List of all available compatibility layers (built-in + custom) as dicts."""
        # Try new key first, fall back to old key for backward compatibility
        return self.__config.get("compatibility_layers", self.__config.get("translators", []))

    @compatibility_layers.setter
    def compatibility_layers(self, new_value: list) -> None:
        # Write both keys for backward compatibility (allows downgrades)
        self.__config["compatibility_layers"] = new_value
        self.__config["translators"] = new_value
        self.__write()

    def add_compatibility_layer(self, layer_dict: dict) -> None:
        layers = self.compatibility_layers
        layers.append(layer_dict)
        self.compatibility_layers = layers

    def remove_compatibility_layer(self, name: str) -> None:
        layers = [t for t in self.compatibility_layers if t.get("name") != name]
        self.compatibility_layers = layers

    # Backward compatibility aliases - deprecated, use compatibility_layers instead
    @property
    def translators(self) -> list:
        """Deprecated: Use compatibility_layers instead."""
        return self.compatibility_layers

    @translators.setter
    def translators(self, new_value: list) -> None:
        """Deprecated: Use compatibility_layers instead."""
        self.compatibility_layers = new_value

    def add_translator(self, translator_dict: dict) -> None:
        """Deprecated: Use add_compatibility_layer instead."""
        self.add_compatibility_layer(translator_dict)

    def remove_translator(self, name: str) -> None:
        """Deprecated: Use remove_compatibility_layer instead."""
        self.remove_compatibility_layer(name)

