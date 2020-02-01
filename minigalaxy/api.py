import time
from urllib.parse import urlencode
import requests
from minigalaxy.game import Game
from minigalaxy.constants import IGNORE_GAME_IDS


class Api:
    def __init__(self, config):
        self.config = config
        self.login_success_url = "https://embed.gog.com/on_login_success"
        self.redirect_uri = "https://embed.gog.com/on_login_success?origin=client"
        self.client_id = "46899977096215655"
        self.client_secret = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"

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
        request_url = "https://auth.gog.com/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        response = requests.get(request_url, params=params)

        response_params = response.json()
        self.active_token = response_params['access_token']
        expires_in = response_params["expires_in"]
        self.active_token_expiration_time = time.time() + int(expires_in)

        return response_params['refresh_token']

    # Get a token based on the code returned by the login screen
    def __get_token(self, login_code: str) -> str:
        request_url = "https://auth.gog.com/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': login_code,
            'redirect_uri': self.redirect_uri,
        }
        response = requests.get(request_url, params=params)

        response_params = response.json()
        self.active_token = response_params['access_token']
        expires_in = response_params["expires_in"]
        self.active_token_expiration_time = time.time() + int(expires_in)

        return response_params['refresh_token']

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
            response = self.request(url, params=params)
            total_pages = response["totalPages"]

            for product in response["products"]:

                if product["id"] not in IGNORE_GAME_IDS:
                    game = Game(name=product["title"], game_id=product["id"], image_url=product["image"])
                    games.append(game)

            if current_page == total_pages:
                all_pages_processed = True
            current_page += 1
        return games

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
    def get_info(self, game: Game) -> tuple:
        request_url = "https://api.gog.com/products/" + str(game.id) + "?expand=downloads,expanded_dlcs,description," \
                                                                       "screenshots,videos,related_products,changelog "
        response = self.request(request_url)

        return response

    def get_link_game(self, game: Game):
        download_links = []
        response = self.get_info(game)
        for installer in response["downloads"]["installers"]:
            for url in installer['files']:
                download_links.append(url['downlink'])
        return download_links

    def check_compatibility(self, game: Game):
        response = self.get_info(game)
        return response["downloads"]["installers"]

    def get_os_game(self, game:Game):
        for os_version in self.check_compatibility(game):
            if os_version["os"] == "linux":
                self.config.set("os_version_" + str(game.id), "linux")
            elif "linux" not in os_version["os"]:
                self.config.set("os_version_" + str(game.id), "windows")

    def get_user_info(self) -> str:
        username = self.config.get("username")
        if not username:
            url = "https://embed.gog.com/userData.json"
            response = self.request(url)
            username = response["username"]
            self.config.set("username", username)
        return username

    def can_connect(self) -> bool:
        url = "https://embed.gog.com"
        try:
            requests.get(url, timeout=5)
        except requests.exceptions.ConnectionError:
            return False
        return True

    # Make a request with the active token
    def request(self, url: str = None, params: dict = None) -> tuple:
        # Refresh the token if needed
        if self.active_token_expiration_time < time.time():
            print("Refreshing token")
            refresh_token = self.config.get("refresh_token")
            self.config.set("refresh_token", self.__refresh_token(refresh_token))

        # Make the request
        headers = {
            'Authorization': "Bearer " + self.active_token,
        }
        response = requests.get(url, headers=headers, params=params)
        return response.json()
