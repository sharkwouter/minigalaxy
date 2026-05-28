from importlib.resources import files
from importlib.resources.abc import Traversable


def get_data_file(file_name: str) -> Traversable:
    """
    A data file, as recommended by https://setuptools.pypa.io/en/latest/userguide/datafiles.html
    """
    return files("minigalaxy.data").joinpath(file_name)


def get_ui_data_file(file_name: str) -> Traversable:
    """
    A UI data file, as recommended by https://setuptools.pypa.io/en/latest/userguide/datafiles.html
    """
    return files("minigalaxy.ui.data").joinpath(file_name)


def platform_name_to_icon_file(name: str):
    if name == "windows":
        return "icon_wine.png"

    return "icon_linux.png"
