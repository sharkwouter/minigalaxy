import os
import json
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
                except json.decoder.JSONDecodeError:
                    print("Reading config.json failed, creating new config file.")
                    os.remove(self.__config_file)

    def __write(self) -> None:
        if not os.path.isfile(self.__config_file):
            config_dir = os.path.dirname(self.__config_file)
            os.makedirs(config_dir, mode=0o700, exist_ok=True)
        temp_file = f"{self.__config_file}.tmp"
        with open(temp_file, "w") as file:
            file.write(json.dumps(self.__config, ensure_ascii=False))
        os.rename(temp_file, self.__config_file)

    def get(self, key: str, default: any = None) -> any:
        return self.__config[key] if key in self.__config else default

    def set(self, key: str, value: any) -> None:
        self.__config[key] = value
        self.__write()

    @property
    def locale(self) -> str:
        return self.get("locale", "")

    @locale.setter
    def locale(self, new_value: str) -> None:
        self.set("locale", new_value)

    @property
    def lang(self) -> str:
        return self.get("lang", "en")

    @lang.setter
    def lang(self, new_value: str) -> None:
        self.set("lang", new_value)

    @property
    def view(self) -> str:
        return self.get("view", "grid")

    @view.setter
    def view(self, new_value: str) -> None:
        self.set("view", new_value)

    @property
    def install_dir(self) -> str:
        return self.get("install_dir", DEFAULT_INSTALL_DIR)

    @install_dir.setter
    def install_dir(self, new_value: str) -> None:
        self.set("install_dir", new_value)

    @property
    def username(self) -> str:
        return self.get("username", "")

    @username.setter
    def username(self, new_value: str) -> None:
        self.set("username", new_value)

    @property
    def refresh_token(self) -> str:
        return self.get("refresh_token", "")

    @refresh_token.setter
    def refresh_token(self, new_value: str) -> None:
        self.set("refresh_token", new_value)

    @property
    def keep_installers(self) -> bool:
        return self.get("keep_installers", False)

    @keep_installers.setter
    def keep_installers(self, new_value: bool) -> None:
        self.set("keep_installers", new_value)

    @property
    def stay_logged_in(self) -> bool:
        return self.get("stay_logged_in", True)

    @stay_logged_in.setter
    def stay_logged_in(self, new_value: bool) -> None:
        self.set("stay_logged_in", new_value)

    @property
    def use_dark_theme(self) -> bool:
        return self.get("use_dark_theme", False)

    @use_dark_theme.setter
    def use_dark_theme(self, new_value: bool) -> None:
        self.set("use_dark_theme", new_value)

    @property
    def show_hidden_games(self) -> bool:
        return self.get("keep_installers", False)

    @show_hidden_games.setter
    def show_hidden_games(self, new_value: bool) -> None:
        self.set("show_hidden_games", new_value)

    @property
    def show_windows_games(self) -> bool:
        return self.get("show_windows_games", False)

    @show_windows_games.setter
    def show_windows_games(self, new_value: bool) -> None:
        self.set("show_windows_games", new_value)

    @property
    def keep_window_maximized(self) -> bool:
        return self.get("keep_window_maximized", False)

    @keep_window_maximized.setter
    def keep_window_maximized(self, new_value: bool) -> None:
        self.set("keep_window_maximized", new_value)

    @property
    def installed_filter(self) -> bool:
        return self.get("installed_filter", False)

    @installed_filter.setter
    def installed_filter(self, new_value: bool) -> None:
        self.set("installed_filter", new_value)

    @property
    def create_applications_file(self) -> bool:
        return self.get("create_applications_file", False)

    @create_applications_file.setter
    def create_applications_file(self, new_value: bool) -> None:
        self.set("create_applications_file", new_value)

    @property
    def current_downloads(self) -> list[int]:
        return self.get("current_downloads", [])

    @current_downloads.setter
    def create_applications_file(self, new_value: list[int]) -> None:
        self.set("current_downloads", new_value)
