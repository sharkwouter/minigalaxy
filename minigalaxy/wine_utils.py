"""Some helpers to handle selection, configuration and start of wine commands"""
import json
import shutil

from urllib import request, parse
from minigalaxy.config import Config
from minigalaxy.constants import WINE_VARIANTS
from minigalaxy.game import Game
from minigalaxy.logger import logger

UMUDB_URL = "https://umu.openwinecomponents.org"

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


def get_wine_env(game: Game, config: Config = Config(), quoted=False) -> []:
    if quoted:
        envPattern = '{key}="{value}"'
    else:
        envPattern = '{key}={value}'

    environment = [ envPattern.format(key='WINEDLLOVERRIDES', value="winemenubuilder.exe=d") ]
    environment.append(envPattern.format(key='WINEPREFIX', value=f"{game.install_dir}/prefix"))

    if 'umu-run' in get_wine_path(game, config):
        environment.append(envPattern.format(key='GAMEID', value=f"{get_umu_id(game)}"))
        if shutil.which('zenity'):
            environment.append('UMU_ZENITY=1')

    for var in game.get_info("variable").split():
        kvp = var.split('=', 1)
        environment.append(envPattern.format(key=kvp[0], value=kvp[1]))

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

def get_umu_id(game: Game) -> str:
    id = game.get_info(GAMEINFO_UMUID)
    if id:
        return id

    lookup_strategies = [
        f'store=gog&codename={game.id}',
        f'store=steam&title={game.name}',
        f'store=none&title={game.name}'
    ]

    api_reachable = False
    for strategy in lookup_strategies:
        try:
            logger.debug(f"Trying to find an UMU-ID for '{game.name}'")
            queryUrl = f'{UMUDB_URL}/umu_api.php?{parse.quote_plus(strategy)}'
            with request.urlopen(queryUrl) as request_result:
                lookup_result = json.loads(request_result.read())
        except:
            api_reachable = api_reachable or False
            continue
        else:
            api_reachable = True

        if lookup_result[0] and lookup_result[0]['umu_id']:
            id = lookup_result[0]['umu_id']
            break

    if not id:
        # this is not a game where any protonfixes are known, make up a sufficiently unique umu-id
        # just to satisfy umu-run. UMUID is only used to search for protonfixes, if any are needed
        # most games should run fine without any fixes
        id = f'umu-gog:{game.id}'

    if api_reachable:
        # only save the id when none of the requested APIs threw an error
        # which that we can temporary try to run the game without protonfixes,
        # but will re-try the api the next time it is started
        game.set_info(GAMEINFO_UMUID, id)
    else:
        logger.warning("UMU-DB not reachable - retry again on next game start")

    return id
