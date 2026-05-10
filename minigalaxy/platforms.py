from minigalaxy.config import Config
from minigalaxy.game import Game


def update_supported_platforms(game: Game, config: Config):
    """Update 'Game.platform' of the given game depending on 'Config.platform_mode' and the install state"""
    if game.is_installed():
        # do nothing, installed games get their platform tag when loading from the install dir
        return

    active_platforms = set(config.platform_mode)
    supported_platforms = list(set(game.supported_platforms()) & active_platforms)

    # temporary: until full platform selection support is merged in the UI, do a forced pre-selection here
    # this block will be removed later and the (reduced) supported_platforms set will be used directly
    if len(supported_platforms) > 1 and config.preferred_platform in supported_platforms:
        supported_platforms = config.preferred_platform
    elif len(supported_platforms) == 1:
        supported_platforms = supported_platforms[0]
    else:
        supported_platforms = []

    game.platform = supported_platforms
