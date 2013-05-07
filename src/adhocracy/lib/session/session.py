import collections
import datetime
try:
    from http.cookies import SimpleCookie
except ImportError: # Python < 3
    from Cookie import SimpleCookie
import logging

from adhocracy.lib.cookie import get_cookies
from adhocracy.lib.session.converter import SignedValueConverter

log = logging.getLogger(name=__name__)

def get_secret(config):
    for k in ['adhocracy.session.secret',
              'beaker.session.secret',
              'adhocracy.auth.secret',]:
        if k in config:
            return config[k]
    raise Exception('No secret configured!')

_PREFIX = u'adhocracy_session_'

class Session(dict):
    """ Stores session specific values on the client site.
        `converter_class` instances must respond to `encode` and `decode`
        messages.
    """

    def __init__(self, environ, config, converter_class=None):
        if converter_class is None:
            converter_class = SignedValueConverter

        if 'adhocracy.session.lifetime' in config:
            self._max_age = int(config.get('adhocracy.session.lifetime'))
        else:
            self._max_age = None

        self._changed = set()
        self._deleted = set()

        secret = get_secret(config)
        self._converter = converter_class(secret)
        self._load_from_cookie(environ)

    def __setitem__(self, key, value):
        self._changed.add(key)
        self._deleted.discard(key)
        return super(Session, self).__setitem__(key, value)

    def __delitem__(self, key):
        self._changed.discard(key)
        self._deleted.add(key)
        super(Session, self).__delitem__(key)

    def _load_from_cookie(self, environ):
        cookie = SimpleCookie(environ.get("HTTP_COOKIE"))
        if cookie:
            for key,c in cookie.items():
                if not key.startswith(_PREFIX):
                    continue
                key = key[len(_PREFIX):]

                val = self._converter.decode(c.value)
                if val is not None:
                    super(Session, self).__setitem__(key, val)

    def set_cookies_in(self, headers):
        changed = dict((_PREFIX + k, self._converter.encode(self[k]))
                       for k in self._changed)
        headers.extend(get_cookies(changed, max_age=self._max_age))

        deleted = dict((_PREFIX + k, 'invalid')
                       for k in self._deleted)
        headers.extend(get_cookies(deleted, max_age='delete'))

    def delete(self):
        self._deleted.update(self.keys())
        self.clear()

    def save(self):
        """ This session implementation does not need this function because the
            values are saved by the client.
        """
        pass

