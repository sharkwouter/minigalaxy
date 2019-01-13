from urllib.parse import urlencode, urlparse, parse_qsl
import requests


class Api:

    login_success_url = "https://embed.gog.com/on_login_success"
    redirect_uri = "https://embed.gog.com/on_login_success?origin=client"

    client_id = "46899977096215655"
    client_secret = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"

    active_token = None
    active_until = None

    # use a method to authenticate, based on the information we have. Returns None if no information was entered
    def authenticate(self, url=None, token=None):
        if token:
            return self.__refresh_token(token)
        elif url:
            return self.__get_token(url)
        else:
            return None

    # Get a new token with the refresh token received when authenticating the last time
    def __refresh_token(self, refresh_token):
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

        return response_params['refresh_token']

    # Get a token based on the url returned by the login screen
    def __get_token(self, oauth_response):
        parsed_url = urlparse(oauth_response)
        input_params = dict(parse_qsl(parsed_url.query))
        code = input_params.get('code')

        request_url = "https://auth.gog.com/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        response = requests.get(request_url, params=params)

        response_params = response.json()
        self.active_token = response_params['access_token']

        return response_params['refresh_token']

    # Get all Linux games in the library of the user. Ignore other platforms and movies
    def get_library(self):
        if not self.active_token:
            return

        url = "https://embed.gog.com/account/getFilteredProducts"
        params = {
            'mediaType': 1,
            'system': '1024', #1024 is Linux
            'page': 1,
        }
        response = self.__request(url, params=params)

        return response

    # Generate the URL for the login page for GOG
    def get_login_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'layout': 'client2',
        }
        return "https://auth.gog.com/auth?" + urlencode(params)

    def get_redirect_url(self):
        return self.redirect_uri

    # This returns a unique download url and a link to the checksum of the download
    def get_download_info(self, game_id):
        url = 'https://api.gog.com/products/{}?expand=downloads'.format(game_id)
        response = self.__request(url)
        for installer in response["downloads"]["installers"]:
            if installer["id"] == "installer_linux_en":
                return self.__request(installer["files"][0]["downlink"])

    # Make a request with the active token
    def __request(self, url=None, params=None):
        headers = {
            'Authorization': "Bearer " + self.active_token,
        }
        response = requests.get(url, headers=headers, params=params)
        return response.json()
