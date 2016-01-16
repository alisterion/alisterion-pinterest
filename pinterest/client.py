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
        "Accept-Language": "en",
        "Accept-Encoding": "gzip",
        "Host": base_url.replace("https://", ""),
        "User-Agent": "Pinterest for Android/1.0.2 (generic_x86; 4.0.4)",
        "X-Pixel-Ratio": "1.5",
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

    # Figure how to selectively enforce access_token here
    def _post_request(self, path, params={}, data={}):
        url = "%s%s" % (self.base_url, path)
        try:
            return requests.post(url, params=params, data=data,
                                 headers=self.headers)
        except exceptions.RequestException as e:
            raise PinterestException(e)

    def me(self):
        """Retrieve the currently authenticated user."""
        path = "/v1/me"
        return self._get_request(path)

    def home(self, page=1, limit=25):
        """Retreive the home feed for the currently authenticated user."""
        path = "/v2/home"
        return self._get_request(path, {"page": page, "limit": limit})

    def boards(self):
        """Retrieve all the boards for the currently authenticated user."""
        path = "/v1/boards"
        return self._get_request(path)

    def board(self, user, board):
        """Retrieve information about the specified user's board."""
        path = "/v2/boards/%s/%s" % (user, board)
        return self._get_request(path)

    def pin(self, pin_id):
        """Retrieve information about a single Pin."""
        path = "/v2/pin/%d" % pin_id
        return self._get_request(path)

    def popular(self, page=1, limit=25):
        """Retrieve a list of popular Pins."""
        path = "/v2/popular"
        return self._get_request(path, {"page": page, "limit": limit})

    def all(self, category=None, page=1, limit=25):
        """Retrieve a list of Pins, possibly from a specific category. Valid
        categories can be determined by the categories() method below.
        """
        path = "/v2/all"
        return self._get_request(path, {"category": category, "page": page,
                                        "limit": limit})

    def videos(self, page=1, limit=25):
        """Retrieve a list of video Pins."""
        path = "/v2/videos"
        return self._get_request(path, {"page": page, "limit": limit})

    def activity(self):
        """Retrieve recent activity information for the currently authenticated user."""
        path = "/v2/activity"
        return self._get_request(path)

    def search(self, query, domain="pins", page=1, limit=25):
        """Search for Pins in the given domain. Domain must be one of the
        following: pins, boards, people.
        """
        path = "/v2/search/%s" % domain
        return self._get_request(path,
                                 {"query": query, "page": page,
                                  "limit": limit})

    def categories(self):
        """Retrieve the list of available categories."""
        path = "/v3/categories"
        return self._get_request(path)

    def user(self, user):
        """Retreive information about the given user."""
        path = "/v2/users/%s" % user
        return self._get_request(path)

    def _user_info(self, user, info_type, page=1, limit=25):
        """Helper method to retrieve specific data for the given user."""
        path = "/v2/users/%s/%s/" % (user, info_type)
        return self._get_request(path, {"page": page, "limit": limit})

    def user_boards(self, user, page=1, limit=25):
        """Retrieve all information about the given user's boards."""
        return self._user_info(user, "boards", page, limit)

    def user_pins(self, user, page=1, limit=25):
        """Retrieve the given user's Pins."""
        return self._user_info(user, "pins", page, limit)

    def user_likes(self, user, page=1, limit=25):
        """Retrieve the given user's Likes."""
        return self._user_info(user, "likes", page, limit)

    def user_about(self, user):
        """Retrieve the about section for the given user."""
        return self._user_info(user, "about")

    def following(self, user):
        """Retrieve the list of users the given user is following. Answers the
        question: Who is <USER> following?
        """
        path = "/v2.1/users/%s/following" % user
        return self._get_request(path)

    def followers(self, user):
        """Retrieve the list of users who are following the given user. Answers
        the question: Who is following <USER>?
        """
        path = "/v2.1/users/%s/followers" % user
        return self._get_request(path)

    def follow(self, user):
        """Request that the currently authenticated user follow another user."""
        raise NotImplementedError()
        path = "/v2/user/%s/follow/" % user
        return self._post_request(path)

    def unfollow(self, user):
        """Request that the currently authenticated user unfollow another user."""
        raise NotImplementedError()
        path = "/v2/user/%s/unfollow/" % user
        return self._post_request(path)

    def repin(self, pin_id, board_id, details=None, publish_facebook=False,
              publish_twitter=False):
        """Repin the specified Pin to the specified Board."""
        raise NotImplementedError()
        path = "/v2/repin/%d/" % pin_id
        data = {
            "board": board_id,
            "detail": details,
            "publish_to_facebook": publish_facebook,
            "publish_to_twitter": publish_twitter
        }
        return self._post_request(path, data=data)

    def like(self, pin_id):
        """Like the specified Pin."""
        raise NotImplementedError()
        path = "/v2/pin/%d/like/" % pin_id
        return self._post_request(path)

    def comment(self, pin_id, text):
        """Leave a comment on the specified Pin."""
        raise NotImplementedError()
        path = "/v2/pin/%d/comment/" % pin_id
        return self._post_request(path, data={"text": text})

    def create_board(self, name, category=None, description=None):
        """Create a new board."""
        raise NotImplementedError()
        path = "/v2/board/create/"
        return self._post_request(path,
                                  data={"name": name, "category": category,
                                        "description": description})


class PinterestException(Exception):
    pass
