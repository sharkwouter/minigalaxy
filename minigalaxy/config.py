import os
import json
from typing import List

from minigalaxy.logger import logger
from minigalaxy.paths import CONFIG_FILE_PATH, DEFAULT_INSTALL_DIR


class Config:

    __config_file: str
    __config: dict

    def __init__(self, config_file: str = CONFIG_FILE_PATH):
        self.__config_file = config_file
        self.__config = {}
        self.__load()

    def __load(self) -> None:
        if os.path.isfile(self.__config_file):
            with open(self.__config_file, "r") as file:
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
        with open(temp_file, "w") as file:
            file.write(json.dumps(self.__config, ensure_ascii=False))
        os.rename(temp_file, self.__config_file)

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
    def default_wine_runner(self) -> str:
        return self.__config.get("default_wine_runner", "wine")

    @default_wine_runner.setter
    def default_wine_runner(self, new_value: str) -> None:
        self.__config["default_wine_runner"] = new_value
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
    def current_downloads(self) -> List[int]:
        return self.__config.get("current_downloads", [])

    @current_downloads.setter
    def current_downloads(self, new_value: List[int]) -> None:
        self.__config["current_downloads"] = new_value
        self.__write()
