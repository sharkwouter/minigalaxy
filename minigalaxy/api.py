from urllib.parse import urlencode, urlparse, parse_qsl
import requests


class Api:

    login_success_url = "https://embed.gog.com/on_login_success"
    redirect_uri = "https://embed.gog.com/on_login_success?origin=client"

    client_id = "46899977096215655"
    client_secret = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"

    active_token = None
    active_until = None

    def authenticate(self, url=None, token=None):
        if token:
            return self.__refresh_token(token)
        elif url:
            return self.__get_token(url)
        else:
            return None

    def __refresh_token(self, token):
        request_url = "https://auth.gog.com/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': token,
        }
        response = requests.get(request_url, params=params)

        response_params = response.json()
        self.active_token = response_params['access_token']

        return response_params['refresh_token']

    def __get_token(self, url):
        parsed_url = urlparse(url)
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

    def get_library(self):
        if not self.active_token:
            return

        url = "https://embed.gog.com/account/getFilteredProducts"
        headers = {
            'Authorization': "Bearer " + self.active_token,
            'Content-Type': "application/json"
        }
        params = {
            'mediaType': 1,
            'system': '1024', #1024 is Linux
            'page': 2,
        }
        response = requests.get(url, headers=headers, params=params)

        return response.json()

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
