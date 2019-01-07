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
        params = {
            'mediaType': 1,
            'system': '1024', #1024 is Linux
            'page': 1,
        }
        response = self.__request(url, params=params)


        return response

    def download(self, id=None):
        if not id:
            return
        url = self.__get_download_url(id)
        file_data = self.__request(url)

        file_url = file_data["downlink"]
        filename = "data/download/{}.sh".format(id)
        headers = {
            'Authorization': "Bearer " + self.active_token,
        }
        data = requests.get(file_url, stream=True, headers=headers)
        handle = open(filename, "wb")
        for chunk in data.iter_content(chunk_size=512):
            if chunk:
                handle.write(chunk)
        handle.close()

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

    def __get_download_url(self, id):
        url = 'https://api.gog.com/products/{}?expand=downloads'.format(id)
        response = self.__request(url)
        for installer in response["downloads"]["installers"]:
            if installer["id"] == "installer_linux_en":
                return_url = installer["files"][0]["downlink"]
                print(str(return_url))
                return return_url

    def __request(self, url=None, params=None):
        headers = {
            'Authorization': "Bearer " + self.active_token,
        }
        response = requests.get(url, headers=headers, params=params)
        return response.json()
