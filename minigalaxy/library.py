'''
Created on 07/05/2020

@author: Miguel Gomes <alka.setzer@gmail.com>
'''
import os
import re
import json
import time
from typing import List
from minigalaxy.api import Api
from minigalaxy.config import Config
from minigalaxy.game import Game
from pickle import TRUE

class Library():

    def __init__(self, api: Api):
        self.api = api
        self.games = []
        self.offline = False
        self.last_api_check = 0;
        
    def __get_installed_games(self) -> List[Game]:
        games = []
        directories = os.listdir(Config.get("install_dir"))
        for directory in directories:
            full_path = os.path.join(Config.get("install_dir"), directory)
            # Only scan directories
            if not os.path.isdir(full_path):
                continue
            # Make sure the gameinfo file exists
            gameinfo = os.path.join(full_path, "gameinfo")
            if os.path.isfile(gameinfo):
                with open(gameinfo, 'r') as file:
                    name = file.readline().strip()
                    version = file.readline().strip()
                    version_dev = file.readline().strip()
                    language = file.readline().strip()
                    game_id = file.readline().strip()
                    if not game_id:
                        game_id = 0
                    else:
                        game_id = int(game_id)
                supported_platforms=[]
                supported_platforms.append("linux")
                games.append(Game(name=name, game_id=game_id, install_dir=full_path, installed = 1, platform="linux", supported_platforms=supported_platforms, installed_version = version))
            else:
                game_files = os.listdir(full_path)
                for file in game_files:
                    if re.match(r'^goggame-[0-9]*\.info$', file):
                        with open(os.path.join(full_path, file), 'r') as info_file:
                            info = json.loads(info_file.read())
                            supported_platforms=[]
                            supported_platforms.append("windows")
                            game = Game(
                                name=info["name"],
                                game_id=int(info["gameId"]),
                                install_dir=full_path,
                                platform="windows",
                                supported_platforms=supported_platforms,
                                installed=1
                            )
                            games.append(game)
        return games
    
    def __validate_if_installed_is_latest(self,game,info) -> bool:
        if (game.installed_version is None or len(game.installed_version) == 0):
            return False
        installers = info["downloads"]["installers"];
        current_installer = None
        for installer in installers: 
            if (installer["os"] != game.platform):
                continue;
            current_installer = installer
            break            
        # validate if we have the latest version
        return (current_installer is not None and current_installer["version"] == game.installed_version)
    
    def __get_games_from_api(self):
        try:
            retrieved_games = self.api.get_library()
            self.offline = False
        except:
            self.offline = True
            return
        for game in retrieved_games:
            if game in self.games:
                # Make sure the game id is set if the game is installed
                for installed_game in self.games:
                    if game == installed_game:
                        game.installed = 1
                        game.install_dir = installed_game.install_dir
                        game.installed_version = installed_game.installed_version
                        # also check if we have the most up to date version or not
                        try:
                            game.updates = 0 if self.__validate_if_installed_is_latest(game,self.api.get_info(game)) == True else 1 
                        except:
                            print("Could not fetch current information about {}".format(game.name))
                        self.games.remove(installed_game)
                        break
            self.games.append(game)
    
    def get_games(self) -> List[Game]:
        # wait a some time before calling the API again
        if (time.time() - self.last_api_check < 30):
            self.last_api_check = time.time()
            return self.games;
        # rebuild list
        self.games = self.__get_installed_games()
        self.__get_games_from_api()
        return self.games

    def get_sorted_games(self, key="game", reverse=False, sortfn = None) -> List[Game]:
        if (sortfn is None):
            return sorted(self.games, key, reverse)
        else:
            return sortfn(self.games, key, reverse)

    def get_filtered_games(self, installed = None, platform = None, category = None, tag = None, name = None) -> List[Game]:
        games = []
        for game in self.games:
            if (self.is_game_filtered(game,installed, platform, category, tag, name) == False):
                continue
            games.append(game)
        return games
       
    def is_game_filtered(self, game, installed = None, platform = None, category = None, tag = None, name = None) -> bool:
        if (installed == True and game.installed == 0):
            return False
        if (platform is not None and platform not in game.supported_platforms):
            return False
        if (category is not None and game.category != category):
            return False
        if (tag is not None and tag not in game.tags):
            return False
        if (name is not None):
            try:
                game.name.lower().index(name.lower())
            except ValueError:
                return False
        return TRUE
