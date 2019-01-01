from urllib.parse import urlencode, urlparse, parse_qsl
import requests
import json

embed_url = 'https://embed.gog.com'
api_url = 'https://api.gog.com'

class GOGAPI():

    def __init__(self):
        self.name = "GOG"
        self.client_id = "46899977096215655"
        self.login_success_url = embed_url + "/on_login_success"
        self.redirect_uri = self.login_success_url + "?origin=client"
        self.client_secret = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"
        self.active_token = None
        self.refresh_token = None

    def get_login_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'layout': 'client2'
        }
        return "https://auth.gog.com/auth?" + urlencode(params)

    def authenticate(self, input_url):

        parsed_url = urlparse(input_url)
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

        print(response.json())

        response_params = response.json()
        self.active_token = response_params['access_token']
        self.save_activate_token()
        self.refresh_token = response_params['refresh_token']
        self.save_refresh_token()

    def refresh(self):
        request_url = "https://auth.gog.com/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        response = requests.get(request_url, params=params)

        print(response.json())

        response_params = response.json()
        self.active_token = response_params['access_token']
        self.save_activate_token()
        self.refresh_token = response_params['refresh_token']
        self.save_refresh_token()

    def save_activate_token(self):
        file = open("activate.txt", "w")
        file.write(self.active_token)
        file.close()

    def read_activate_token(self):
        file = open("activate.txt", "r")
        self.active_token = file.read()
        file.close()

    def save_refresh_token(self):
        file = open("refresh.txt", "w")
        file.write(self.refresh_token)
        file.close()

    def read_refresh_token(self):
        file = open("refresh.txt", "r")
        self.refresh_token = file.read()
        file.close()

    def get_library(self):
        if self.active_token is None:
            return
        url = "https://embed.gog.com/account/getFilteredProducts"
        headers = {
            'Authorization': "Bearer " + self.active_token,
            'Content-Type': "application/json"
        }
        params = {
            'mediaType': 1,
            'system': '1024', #1024 is Linux
        }
        response = requests.get(url, headers=headers, params=params)
        print(response.json())

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_name(self):
        return self.name
