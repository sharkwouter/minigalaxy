import os
import time
from urllib.parse import urlencode
import requests
import xml.etree.ElementTree as ET
from minigalaxy.game import Game
from minigalaxy.constants import IGNORE_GAME_IDS, SESSION
from minigalaxy.config import Config


class NoDownloadLinkFound(BaseException):
    pass


class Api:
    def __init__(self):
        self.login_success_url = "https://embed.gog.com/on_login_success"
        self.redirect_uri = "https://embed.gog.com/on_login_success?origin=client"
        self.client_id = "46899977096215655"
        self.client_secret = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"
        self.debug = os.environ.get("MG_DEBUG")
        self.active_token = False
        self.active_token_expiration_time = time.time()

    # use a method to authenticate, based on the information we have
    # Returns an empty string if no information was entered
    def authenticate(self, login_code: str = None, refresh_token: str = None) -> str:
        if refresh_token:
            return self.__refresh_token(refresh_token)
        elif login_code:
            return self.__get_token(login_code)
        else:
            return ''

    # Get a new token with the refresh token received when authenticating the last time
    def __refresh_token(self, refresh_token: str) -> str:
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        response_token = self.__get_refresh_token(params)
        return response_token

    # Get a token based on the code returned by the login screen
    def __get_token(self, login_code: str) -> str:
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': login_code,
            'redirect_uri': self.redirect_uri,
        }
        response_token = self.__get_refresh_token(params)
        return response_token

    def __get_refresh_token(self, params: dict) -> str:
        request_url = "https://auth.gog.com/token"
        response = SESSION.get(request_url, params=params)
        response_params = response.json()
        if "access_token" in response_params and "expires_in" in response_params and "refresh_token" in response_params:
            self.active_token = response_params["access_token"]
            expires_in = response_params["expires_in"]
            self.active_token_expiration_time = time.time() + int(expires_in)
            refresh_token = response_params["refresh_token"]
        else:
            refresh_token = ""
        return refresh_token

    # Get all Linux games in the library of the user. Ignore other platforms and movies
    def get_library(self):
        if not self.active_token:
            return

        games = []
        current_page = 1
        all_pages_processed = False
        url = "https://embed.gog.com/account/getFilteredProducts"

        while not all_pages_processed:
            params = {
                'mediaType': 1,  # 1 means game
                'page': current_page,
            }
            response = self.__request(url, params=params)
            total_pages = response["totalPages"]

            for product in response["products"]:
                if product["id"] not in IGNORE_GAME_IDS:
                    # Only support Linux unless the show_windows_games setting is enabled
                    if product["worksOn"]["Linux"]:
                        platform = "linux"
                    elif Config.get("show_windows_games"):
                        platform = "windows"
                    else:
                        continue
                    if not product["url"]:
                        print("{} ({}) has no store page url".format(product["title"], product['id']))
                    game = Game(name=product["title"], url=product["url"], game_id=product["id"],
                                image_url=product["image"], platform=platform)
                    games.append(game)
            if current_page == total_pages:
                all_pages_processed = True
            current_page += 1
        return games

    def get_owned_products_ids(self):
        if not self.active_token:
            return
        url2 = "https://embed.gog.com/user/data/games"
        response2 = self.__request(url2)
        return response2["owned"]

    # Generate the URL for the login page for GOG
    def get_login_url(self) -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'layout': 'client2',
        }
        return "https://auth.gog.com/auth?" + urlencode(params)

    def get_redirect_url(self) -> str:
        return self.redirect_uri

    # Get Extrainfo about a game
    def get_info(self, game: Game) -> dict:
        request_url = "https://api.gog.com/products/{}?expand=downloads,expanded_dlcs,description,screenshots,videos," \
                      "related_products,changelog ".format(str(game.id))
        response = self.__request(request_url)
        return response

    # This returns a unique download url and a link to the checksum of the download
    def get_download_info(self, game: Game, operating_system="linux", dlc_installers="") -> tuple:
        if dlc_installers:
            installers = dlc_installers
        else:
            response = self.get_info(game)
            installers = response["downloads"]["installers"]
        possible_downloads = []
        for installer in installers:
            if installer["os"] == operating_system:
                possible_downloads.append(installer)
        if not possible_downloads:
            if operating_system == "linux":
                return self.get_download_info(game, "windows")
            else:
                raise NoDownloadLinkFound("Error: {} with id {} couldn't be installed".format(game.name, game.id))

        download_info = possible_downloads[0]
        for installer in possible_downloads:
            if installer['language'] == Config.get("lang"):
                download_info = installer
                break
            if installer['language'] == "en":
                download_info = installer

        # Return last entry in possible_downloads. This will either be English or the first langauge in the list
        # This is just a backup, if the preferred language has been found, this part won't execute
        return download_info

    def get_real_download_link(self, url):
        return self.__request(url)['downlink']

    def get_download_file_md5(self, url):
        xml_link = self.__request(url)['checksum']
        xml_string = SESSION.get(xml_link).text
        root = ET.fromstring(xml_string)
        return root.attrib['md5']

    def get_user_info(self) -> str:
        username = Config.get("username")
        if not username:
            url = "https://embed.gog.com/userData.json"
            response = self.__request(url)
            username = response["username"]
            Config.set("username", username)
        return username

    def get_version(self, game: Game, gameinfo=None, dlc_name="") -> str:
        if gameinfo is None:
            gameinfo = self.get_info(game)
        version = "0"
        if dlc_name:
            installers = {}
            for dlc in gameinfo["expanded_dlcs"]:
                if dlc["title"] == dlc_name:
                    installers = dlc["downloads"]["installers"]
                    break
        else:
            installers = gameinfo["downloads"]["installers"]
        for installer in installers:
            if installer["os"] == game.platform:
                version = installer["version"]
                break
        return version

    def can_connect(self) -> bool:
        url = "https://embed.gog.com"
        try:
            SESSION.get(url, timeout=5)
        except requests.exceptions.ConnectionError:
            return False
        return True

    # Make a request with the active token
    def __request(self, url: str = None, params: dict = None) -> dict:
        # Refresh the token if needed
        if self.active_token_expiration_time < time.time():
            print("Refreshing token")
            refresh_token = Config.get("refresh_token")
            Config.set("refresh_token", self.__refresh_token(refresh_token))

        # Make the request
        headers = {
            'Authorization': "Bearer {}".format(str(self.active_token)),
        }
        response = SESSION.get(url, headers=headers, params=params)
        if self.debug:
            print("Request: {}".format(url))
            print("Return code: {}".format(response.status_code))
            print("Response body: {}".format(response.text))
            print("")
        return response.json()

    @staticmethod
    def __request_gamesdb(game: Game):
        request_url = "https://gamesdb.gog.com/platforms/gog/external_releases/{}".format(game.id)
        try:
            response = SESSION.get(request_url)
            respones_dict = response.json()
        except (requests.exceptions.ConnectionError, ValueError):
            respones_dict = {}
        return respones_dict

    def get_gamesdb_info(self, game: Game) -> dict:
        gamesdb_dict = {"cover": "", "vertical_cover": "", "background": ""}
        response_json = self.__request_gamesdb(game)
        if "game" in response_json:
            for gamesdb_key in gamesdb_dict:
                if gamesdb_key in response_json['game']:
                    gamesdb_dict[gamesdb_key] = response_json["game"][gamesdb_key]["url_format"].replace(
                        '{formatter}.{ext}', '.png')
            gamesdb_dict["summary"] = response_json["game"]["summary"]["*"]
        else:
            gamesdb_dict["summary"] = ""
        print(gamesdb_dict)
        return gamesdb_dict
