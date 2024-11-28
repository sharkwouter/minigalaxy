"""Some helpers to handle selection, configuration and start of wine commands"""
import shutil
import textwrap

from minigalaxy.config import Config
from minigalaxy.constants import WINE_VARIANTS
from minigalaxy.game import Game


GAMEINFO_UMUID = "umu_id"
GAMEINFO_CUSTOM_WINE = "custom_wine"


def is_wine_installed() -> bool:
    for wine in WINE_VARIANTS:
        if shutil.which(wine[0]):
            return True
    return False


def get_wine_path(game: Game, config: Config = Config()) -> str:
    custom_wine_path = game.get_info(GAMEINFO_CUSTOM_WINE)
    if custom_wine_path and shutil.which(custom_wine_path):
        return custom_wine_path

    newDefault = get_default_wine(config)
    game.set_info(GAMEINFO_CUSTOM_WINE, newDefault)
    return newDefault


def get_wine_env(game: Game, config: Config = Config()) -> []:
    environment = ['WINEDLLOVERRIDES="winemenubuilder.exe=d"']
    environment.append(f'WINEPREFIX="{game.install_dir}/prefix"')

    if 'umu-run' in get_wine_path(game, config):
        environment.append(f'GAMEID="get_umu_id"')
        if shutil.which('zenity'):
            environment.append('UMU_ZENITY=1')

    for var in game.get_info("variable").split():
        kvp = var.split('=', 1)
        environment.append(f'{[kvp[0]]}="{kvp[1]}"')

    return environment


def get_default_wine(config: Config = Config()) -> str:
    runner = shutil.which(config.default_wine_runner)
    if runner:
        return runner

    # fallback: iterate through all known variants in declaration order
    for option in WINE_VARIANTS:
        runner = shutil.which(option[0])
        if runner:
            return runner

    # should never happen when get_default_wine is used after is_wine_installed returns true
    return ""

