
from pylons import config

from twitter import Api
from oauth import oauth

from adhocracy.contrib.oauthtwitter import OAuthApi

def system_user():
    return config.get('adhocracy.twitter.username')

def create_api(username=None, password=None):
    if not (username and password):
        username = config.get('adhocracy.twitter.username')
        password = config.get('adhocracy.twitter.password')
    return Api(username=username, password=password)

def create_oauth(key=None, secret=None):
    token = None
    if key and secret:
        token = oauth.OAuthToken(key, secret)
    return OAuthApi(consumer_key=config.get('adhocracy.twitter.consumer_key'),
                    consumer_secret=config.get('adhocracy.twitter.consumer_secret'),
                    access_token=token)
    


