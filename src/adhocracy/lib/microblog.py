import json
from urllib2 import urlopen
from urllib import urlencode

from oauth import oauth
from pylons import config

from adhocracy.contrib.oauthtwitter import OAuthApi
from adhocracy.lib.cache import memoize

SHORTENER_URL = "http://api.bit.ly/shorten"

# No, I am not trying to spy on you but simply want to get around
# the nuisance of bit.ly API keys.
DEFAULT_SHORTENER_USER = "pudo"
DEFAULT_SHORTENER_KEY = "R_b3085006e627e897970d7bdd1d4fda95"


def system_user():
    return config.get('adhocracy.twitter.username')


def create_default():
    key = config.get('adhocracy.twitter.key')
    secret = config.get('adhocracy.twitter.secret')
    return create_oauth(key, secret)


def create_oauth(key=None, secret=None):
    token = None
    if key and secret:
        token = oauth.OAuthToken(key, secret)
    return OAuthApi(consumer_key=config.get('adhocracy.twitter.consumer_key'),
                    consumer_secret=config.get(
                        'adhocracy.twitter.consumer_secret'),
                    access_token=token)


@memoize('short_url')
def shorten_url(url):
    try:
        query = urlencode({
            'login': config.get('adhocracy.bitly.login',
                                DEFAULT_SHORTENER_USER),
            'apiKey': config.get('adhocracy.bitly.key',
                                 DEFAULT_SHORTENER_KEY),
            'longUrl': url.encode('utf-8'),
            'format': 'json',
            'version': '2.0.1'})
        request_url = SHORTENER_URL + "?" + str(query)
        data = json.loads(urlopen(request_url).read())
        if not data['statusCode'] == 'OK':
            return url
        return data['results'][url]['shortUrl']
    except:
        return url
