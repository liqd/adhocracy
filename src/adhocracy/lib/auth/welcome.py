""" Automatically log in an invited user """

import re

import adhocracy.model as model
from adhocracy.lib.auth.authorization import has

from paste.deploy.converters import asbool
import pylons
from repoze.who.interfaces import IAuthenticator, IIdentifier
from webob.exc import HTTPFound
from zope.interface import implements


def welcome_enabled(config=pylons.config):
    return asbool(config.get('adhocracy.enable_welcome', 'False'))


def can_welcome():
    """ Can the current user set welcome codes? """
    return welcome_enabled() and has('global.admin')


class WelcomeRepozeWho(object):
    implements(IAuthenticator, IIdentifier)

    def __init__(self, config, rememberer_name, prefix='/welcome/'):
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
        if not u or not u.welcome_code or u.password:
            return None
        if u.welcome_code != m.group('code'):
            return None

        from adhocracy.lib.helpers import base_url
        root_url = base_url('/', instance=None, absolute=True,
                            config=self.config)
        environ['repoze.who.application'] = HTTPFound(location=root_url)

        return {
            'repoze.who.plugins.welcome.userid': u.user_name,
        }

    def forget(self, environ, identity):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer.forget(environ, identity)

    def remember(self, environ, identity):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer.remember(environ, identity)

    def authenticate(self, environ, identity):
        userid = identity.get('repoze.who.plugins.welcome.userid')
        if userid is None:
            return None
        identity['repoze.who.userid'] = userid
        return userid


def setup_auth(config, idenitifiers, authenticators):
    if not welcome_enabled(config):
        return

    welcome_rwho = WelcomeRepozeWho(config, 'auth_tkt')
    idenitifiers.append(('welcome', welcome_rwho))
    authenticators.append(('welcome', welcome_rwho))
