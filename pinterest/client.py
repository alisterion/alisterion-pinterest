import time
import json
from urllib.parse import urlencode
import requests
from requests import exceptions


def ensure_access_token(f):
    def g(self, *args, **kwargs):
        if not self.access_token:
            raise PinterestException(
                    "You need an access token to make that call")
        return f(self, *args, **kwargs)

    return g


class PinterestOAuth(object):
    pinterest_url = "https://api.pinterest.com"
    access_token_request_url = "/oauth/?"
    access_token_url = "/v1/oauth/token?"

    scope = (
        "read_public",
        "write_public"
    )

    @staticmethod
    def make_requests(url, params={}):
        try:
            response = requests.post(url, params=params)
        except exceptions.RequestException as e:
            raise PinterestException(e)

        return response.json()

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def auth(self, code):
        params = dict(
                grant_type="authorization_code",
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=code,
        )

        url = "%s%s%s" % (
            self.pinterest_url,
            self.access_token_url,
            urlencode(params)
        )
        resp = self.make_requests(url)
        return resp

    def get_access_token(self, redirect_uri):
        params = dict(
                response_type="code",
                redirect_uri=redirect_uri,
                client_id=self.client_id,
                scope=",".join(self.scope)
        )

        return "%s%s%s" % (
            self.pinterest_url,
            self.access_token_request_url,
            urlencode(params)
        )


class PinterestAPI(object):
    base_url = "https://api.pinterest.com"
    authorize_url = "%s/oauth/authorize" % base_url
    access_token_url = "%s/oauth/access_token" % base_url
    headers = {
        # "Accept-Language": "en",
        # "Accept-Encoding": "gzip",
        # "Host": base_url.replace("https://", ""),
        # "User-Agent": "Pinterest for Android/1.0.2 (generic_x86; 4.0.4)",
        # "X-Pixel-Ratio": "1.5",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    def __init__(self, access_token=None):
        self.access_token = access_token

    @ensure_access_token
    def _get_request(self, path, params={}):
        params["access_token"] = self.access_token
        url = "%s%s" % (self.base_url, path)
        try:
            response = requests.get(url, params=params,
                                    headers=self.headers)
        except exceptions.RequestException as e:
            raise PinterestException(e)

        return json.loads(response.text)

    @ensure_access_token
    def _post_request(self, path, data, params={}):
        params["access_token"] = self.access_token
        url = "%s%s?%s" % (self.base_url, path, urlencode(params))
        try:
            response = requests.post(url, data=data, headers=self.headers)
        except exceptions.RequestException as e:
            raise PinterestException(e)

        return response.json()

    def me(self, fields=None):
        """Description: Return the logged in user's information"""
        path = "/v1/me"
        if fields:
            path = "%s/?%s" % (path, urlencode({"fields": ",".join(fields)}))
        return self._get_request(path)

    def boards(self, fields=None):
        """Retrieve all the boards for the currently authenticated user."""
        path = "/v1/me/boards/"
        if fields:
            path = "%s/?%s" % (path, urlencode({"fields": ",".join(fields)}))
        return self._get_request(path)

    def board(self, board):
        """Retrieve information about the specified user's board."""
        path = "/v1/boards/%s" % board
        return self._get_request(path)

    def pins(self, board, note, image=None, link=None, image_url=None,
             image_base64=None):
        path = "/v1/pins/"
        data = {
            "board": board,
            "note": note,
        }

        if image:
            data.update({"image": image})

        if image_url:
            data.update({"image_url": image_url})

        if image_base64:
            data.update({"image_base64": image_base64})

        resp = self._post_request(path, data)
        return resp

    def pin(self, pin, fields=None):
        path = "/v1/pins/%s" % pin
        if fields:
            path = "%s/?%s" % (path, urlencode({"fields": ",".join(fields)}))
        return self._get_request(path)


class PinterestException(Exception):
    pass
