try:
    from http.cookies import SimpleCookie
except ImportError:  # Python < 3
    from Cookie import SimpleCookie
import logging
import time

from adhocracy.lib.cookie import get_cookie
from adhocracy.lib.session.converter import SignedValueConverter

log = logging.getLogger(name=__name__)
COOKIE_KEY = u'adhocracy_session'


def get_secret(config):
    for k in ('adhocracy.session.secret',
              'beaker.session.secret',
              'adhocracy.auth.secret'):
        if config.get(k):
            return config[k]
    raise Exception('No secret configured!')


class Session(dict):
    """ Stores session specific values on the client site.
        `converter_class` instances must respond to `encode` and `decode`
        messages.
    """

    def __init__(self, environ, config, converter_class=None):
        if converter_class is None:
            converter_class = SignedValueConverter

        self._max_age = int(config.get('adhocracy.session.lifetime',
                                       60 * 60 * 24 * 365))
        self._changed = False

        secret = get_secret(config)
        self._converter = converter_class(secret)
        self._load_from_cookie(environ)

    def __setitem__(self, key, value):
        self._changed = True
        return super(Session, self).__setitem__(key, value)

    def __delitem__(self, key):
        self._changed = True
        super(Session, self).__delitem__(key)

    def _load_from_cookie(self, environ):
        cookie = SimpleCookie(environ.get("HTTP_COOKIE"))
        if not cookie:
            return
        morsel = cookie.get(COOKIE_KEY)
        if not morsel:
            return

        val = self._converter.decode(morsel.value)
        if not val:
            return
        assert isinstance(val, dict)

        if val['__creation'] + self._max_age < time.time():
            # Session has expired
            val = {}

        self.clear()
        self.update(val)
        self._changed = False

    def set_cookies_in(self, headers):
        if not self._changed:
            return
        self['__creation'] = int(time.time())
        val = self._converter.encode(self)
        c = get_cookie(COOKIE_KEY, val, max_age=self._max_age)
        headers.append(c)

    def delete(self):
        self._changed = True
        self.clear()

    def save(self):
        """ This session implementation does not need this function because the
            values are saved by the client.
        """
        pass
