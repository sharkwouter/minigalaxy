from urllib.parse import urlencode


class GOGAPI():

    def __init__(self):
        self.name = "GOG"
        self.client_id = "46899977096215655"
        self.login_success_url = "https://embed.gog.com/on_login_success"
        self.redirect_uri = self.login_success_url + "?origin=client"
        self.client_secret = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"

    def get_login_url(self):
        params = {
            'client_id': self.client_id,
            'layout': 'client2',
            'redirect_uri': self.redirect_uri,
            'response_type': 'code'
        }
        return "https://auth.gog.com/auth?" + urlencode(params)

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_name(self):
        return self.name
