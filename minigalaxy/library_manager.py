from minigalaxy.api import Api
from minigalaxy.entity.game import Game


class LibraryManager:

    def __init__(self, api: Api, config: 'Config'):
        self.api = api
        self.config = config

    def find_games(self) -> list[Game]:
        self.api.get_library()

    def find_games_api(self) -> list[Game]:
        pass

    def find_games_install_directory(self) -> list[Game]:
        pass

    def find_games_cached(self) -> list[Game]:
        pass
