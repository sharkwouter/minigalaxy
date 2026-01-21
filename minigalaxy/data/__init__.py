from importlib.resources import files
from importlib.resources.abc import Traversable

def get_data_file(file_name: str) -> Traversable:
    """
    A data file, as recommended by https://setuptools.pypa.io/en/latest/userguide/datafiles.html
    """
    return files(__package__).joinpath(file_name)
