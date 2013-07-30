""" Logs in user via email """

import re
import adhocracy.model as model
from adhocracy.lib.auth.authorization import has
from paste.deploy.converters import asbool
import pylons
from repoze.who.interfaces import IAuthenticator, IIdentifier
from webob.exc import HTTPFound
from zope.interface import implements
import time
import hashlib
import base64
from adhocracy.lib.crypto import get_secret,sign,verify

def email_url(user, code):
    from adhocracy.lib.helpers import base_url
    return base_url("/emaillogin/%s/%s" % (user.user_name, code),
                    absolute=True)


def create_token(email, config):
    secret = get_secret(config)
    timestamp = str(int(time.time()))
    message =  sign((email + "_" + timestamp).encode("utf-8"),secret)
    return base64.urlsafe_b64encode(message.encode("utf-8"))


def validate_token(user_token, email, config):
    try:
        decoded = base64.urlsafe_b64decode(user_token)
        secret = get_secret(config)
        if config.get('adhocracy.email_login_timer'):
            max_time = config.get('adhocracy.email_login_timer')
        else:
            max_time = 3600
        val = verify((decoded).encode("utf-8"),secret)
        if val:
            user_time = decoded.split('_')[1]
            time_dif = int(time.time()) - int(user_time)
            if int(time_dif) < int(max_time):
                return True
    except (TypeError, ValueError,IndexError):
        return False        
    return False


class EmailLoginRepozeWho(object):
    implements(IAuthenticator, IIdentifier)

    def __init__(self, config, rememberer_name, prefix='/emaillogin/'):
        self.config = config
        self.rememberer_name = rememberer_name
        self.url_rex = re.compile(r'^' + re.escape(prefix) +
                                  r'(?P<id>[^/]+)/(?P<code>[^/]+)$')

    def identify(self, environ):
        path_info = environ['PATH_INFO']
        m = self.url_rex.match(path_info)
        if not m:
            return None
        u = model.User.find(m.group('id'))
        if not u:
            return None

        if not validate_token(m.group('code'), u.email, self.config):
            return None

        from adhocracy.lib.helpers import base_url
        root_url = base_url('/', instance=None, config=self.config)
        environ['repoze.who.application'] = HTTPFound(location=root_url)
        return {
            'repoze.who.plugins.emaillogin.userid': u.user_name,
        }

    def forget(self, environ, identity):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer.forget(environ, identity)

    def remember(self, environ, identity):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer.remember(environ, identity)

    def authenticate(self, environ, identity):
        userid = identity.get('repoze.who.plugins.emaillogin.userid')
        if userid is None:
            return None
        identity['repoze.who.userid'] = userid
        return userid


def setup_auth(config, idenitifiers, authenticators):
    email_rwho = EmailLoginRepozeWho(config, 'auth_tkt')
    idenitifiers.append(('emaillogin', email_rwho))
    authenticators.append(('emaillogin', email_rwho))
