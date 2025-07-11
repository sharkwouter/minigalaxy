import http
import os
import time
from urllib.parse import urlencode
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

from requests import Session

from minigalaxy.file_info import FileInfo
from minigalaxy.game import Game
from minigalaxy.constants import IGNORE_GAME_IDS
from minigalaxy.config import Config
from minigalaxy.logger import logger


class NoDownloadLinkFound(BaseException):
    pass


class Api:
    def __init__(self, config: Config, session: Session):
        self.config = config
        self.session = session
        self.login_success_url = "https://embed.gog.com/on_login_success"
        self.redirect_uri = "https://embed.gog.com/on_login_success?origin=client"
        self.client_id = "46899977096215655"
        self.client_secret = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"
        self.debug = os.environ.get("MG_DEBUG")
        self.active_token = False
        self.active_token_expiration_time = time.time()
        self.conn_check_thpool = ThreadPoolExecutor(max_workers=2)

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
        response = self.session.get(request_url, params=params)
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
        err_msg = ""
        games = []
        if self.active_token:
            current_page = 1
            all_pages_processed = False
            url = "https://embed.gog.com/account/getFilteredProducts"

            while not all_pages_processed:
                params = {
                    'mediaType': 1,  # 1 means game
                    'page': current_page,
                }
                response = self.__request(url, params=params)
                if "totalPages" not in response:
                    err_msg = "Couldn't load game library"
                    return games, err_msg
                total_pages = response["totalPages"]

                for product in response["products"]:
                    if product["id"] not in IGNORE_GAME_IDS:
                        # Only support Linux unless the show_windows_games setting is enabled
                        if product["worksOn"]["Linux"]:
                            platform = "linux"
                        elif self.config.show_windows_games:
                            platform = "windows"
                        else:
                            continue
                        if not product["url"]:
                            logger.warning("{} ({}) has no store page url".format(product["title"], product['id']))
                        game = Game(name=product["title"], url=product["url"], game_id=product["id"],
                                    image_url=product["image"], platform=platform, category=product["category"])
                        games.append(game)
                if current_page == total_pages:
                    all_pages_processed = True
                current_page += 1
        else:
            err_msg = "Couldn't connect to GOG servers"
        return games, err_msg

    def get_owned_products_ids(self):
        if not self.active_token:
            return
        url2 = "https://embed.gog.com/user/data/games"
        response2 = self.__request(url2)
        if "owned" in response2:
            return response2["owned"]

        logger.error("Could not load owned games")
        return []

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
        request_url = "https://api.gog.com/products/{}?locale=en-US&expand=downloads,expanded_dlcs,description,screenshots," \
                      "videos,related_products,changelog".format(str(game.id))
        response = self.__request(request_url)
        return response

    def get_dlc_info(self, game: Game, dlc_id):
        full_info = self.get_info(game)
        dlc_infos = full_info.get("expanded_dlcs", [])
        for dlc in dlc_infos:
            if dlc.get('id', -1) == dlc_id:
                return dlc

    # This returns a unique download url and a link to the checksum of the download
    def get_download_info(self, game: Game, operating_system="linux", dlc_installers="", dlc_id="") -> dict:
        if dlc_installers:
            installers = dlc_installers
        elif dlc_id:
            response = self.get_dlc_info(game, dlc_id)
            installers = response["downloads"]["installers"]
        else:
            response = self.get_info(game)
            installers = response["downloads"]["installers"]
        possible_downloads = []
        for installer in installers:
            if installer["os"] == operating_system:
                possible_downloads.append(installer)
        if not possible_downloads:
            if operating_system == "linux":
                return self.get_download_info(game, "windows", dlc_installers)
            else:
                raise NoDownloadLinkFound("Error: {} with id {} couldn't be installed".format(game.name, game.id))

        download_info = possible_downloads[-1]
        for installer in possible_downloads:
            if installer['language'] == self.config.lang:
                download_info = installer
                break
            if installer['language'] == "en":
                download_info = installer

        # Return last entry in possible_downloads. This will either be English or the first language in the list
        # This is just a backup, if the preferred language has been found, this part won't execute
        return download_info

    def get_real_download_link(self, url):
        return self.__request(url)['downlink']

    def get_download_file_info(self, url):
        """
        Returns some information about a downloadable file based on an XML file offered by GOG
        :param url: Url to get download and checksum links from the API
        :return: a FileInfo object with md5 set to the md5 or and empty string and size set to the file size or 0
        """
        file_info = FileInfo(md5="", size=0)
        try:
            checksum_data = self.__request(url)
            if 'checksum' in checksum_data.keys() and len(checksum_data['checksum']) > 0:
                xml_data = self.__get_xml_checksum(checksum_data['checksum'])
                if "md5" in xml_data.keys() and len(xml_data["md5"]) > 0:
                    file_info.md5 = xml_data["md5"]
                if "total_size" in xml_data.keys() and len(xml_data["total_size"]) > 0:
                    file_info.size = int(xml_data["total_size"])
        except requests.exceptions.RequestException:
            logger.error("Couldn't retrieve file info. Encountered HTTP exception: {}", exc_info=1)

        if not file_info.md5:
            logger.warning("Couldn't find md5 in xml checksum data")

        if not file_info.size:
            logger.warning("Couldn't find file size in xml checksum data")

        return file_info

    def __get_xml_checksum(self, url):
        result = {}
        try:
            response = self.session.get(url)
            if response.status_code == http.HTTPStatus.OK and len(response.text) > 0:
                response_object = ET.fromstring(response.text)
                if response_object and response_object.attrib:
                    result = response_object.attrib
            else:
                logger.error("Couldn't read xml data. Response with code %s received with the following content: %s",
                             response.status_code, response.text, exc_info=1)
        except requests.exceptions.RequestException:
            logger.error("Couldn't read xml data. Received RequestException", exc_info=1)
        finally:
            return result

    def get_user_info(self) -> str:
        username = self.config.username
        if not username:
            url = "https://embed.gog.com/userData.json"
            response = self.__request(url)
            if "username" in response.keys():
                username = response["username"]
                self.config.username = username
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
        urls = [
            "https://embed.gog.com",
            "https://auth.gog.com",
        ]
        threads = []

        def make_request(url_to_check: str):
            try:
                self.session.get(url_to_check, timeout=5)
                return True
            except requests.exceptions.ConnectionError:
                return False

        for url in urls:
            threads.append(self.conn_check_thpool.submit(make_request, url))

        results = []
        for thread in as_completed(threads):
            if thread.cancelled():
                return False
            results += [thread.result()]
        return all(results)

    # Make a request with the active token
    def __request(self, url: str = None, params: dict = None) -> dict:
        # Refresh the token if needed
        if self.active_token_expiration_time < time.time():
            logger.debug("Refreshing token")
            refresh_token = self.config.refresh_token
            self.config.refresh_token = self.__refresh_token(refresh_token)

        # Make the request
        headers = {
            'Authorization': "Bearer {}".format(str(self.active_token)),
        }
        result = {}
        try:
            response = self.session.get(url, headers=headers, params=params)
            if self.debug:
                logger.debug("Request %s, return code %s, response body %s", url, response.status_code, response.text)
            if response.status_code < 300:
                result = response.json()
        except requests.exceptions.RequestException:
            logger.error("Encountered exception while making HTTP request. Request: %s", url, exc_info=1)
        return result

    def __request_gamesdb(self, game: Game):
        request_url = "https://gamesdb.gog.com/platforms/gog/external_releases/{}".format(game.id)
        try:
            response = self.session.get(request_url)
            response_dict = response.json()
        except (requests.exceptions.ConnectionError, ValueError):
            logger.error("Error retrieving game info for gamesdb", exc_info=1)
            response_dict = {}
        return response_dict

    def get_gamesdb_info(self, game: Game) -> dict:
        gamesdb_dict = {"cover": "", "vertical_cover": "", "background": ""}
        response_json = self.__request_gamesdb(game)
        if "game" in response_json:
            for gamesdb_key in gamesdb_dict:
                if gamesdb_key in response_json['game']:
                    gamesdb_dict[gamesdb_key] = response_json["game"][gamesdb_key]["url_format"].replace(
                        '{formatter}.{ext}', '.png')
            gamesdb_dict["summary"] = {}
            for summary_key in response_json["game"]["summary"]:
                gamesdb_dict["summary"][summary_key] = response_json["game"]["summary"][summary_key]
            gamesdb_dict["genre"] = {}
            if len(response_json["game"]["genres"]) > 0:
                for genre in response_json["game"]["genres"]:
                    for genre_key, genre_value in genre["name"].items():
                        if genre_key in gamesdb_dict["genre"] and len(gamesdb_dict["genre"][genre_key]) > 0:
                            gamesdb_dict["genre"][genre_key] += ', '
                        else:
                            gamesdb_dict["genre"][genre_key] = ''
                        gamesdb_dict["genre"][genre_key] += genre["name"][genre_key]
        else:
            gamesdb_dict["summary"] = {}
            gamesdb_dict["genre"] = {}
        return gamesdb_dict
