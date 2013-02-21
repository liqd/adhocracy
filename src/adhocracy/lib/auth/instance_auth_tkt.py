import datetime
import re
from paste.deploy.converters import asbool
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin, _now

# Valid cookie values, see http://tools.ietf.org/html/rfc6265#section-4.1.1
_COOKIE_VALUE_RE = re.compile(u'^[!#$%&\'()*+./0-9:<=>?@A-Z[\\]^_`a-z{|}~-]*$')


class InstanceAuthTktCookiePlugin(AuthTktCookiePlugin):
    def __init__(self, config, *args, **kwargs):
        super(InstanceAuthTktCookiePlugin, self).__init__(*args, **kwargs)
        self.__config = config

    def _get_cookies(self, environ, value, max_age=None):
        assert _COOKIE_VALUE_RE.match(value)
        if max_age is not None:
            later = _now() + datetime.timedelta(seconds=int(max_age))
            # Wdy, DD-Mon-YY HH:MM:SS GMT
            expires = later.strftime('%a, %d %b %Y %H:%M:%S')
            # the Expires header is *required* at least for IE7 (IE7 does
            # not respect Max-Age)
            max_age = "; Max-Age=%s; Expires=%s" % (max_age, expires)
        else:
            max_age = ''

        secure = ''
        if self.secure:
            secure = ' ; secure'

        if asbool(self.__config.get('adhocracy.relative_urls', 'false')):
            # Serve the cookie for the current host, which may be
            # "localhost" or an IP address.
            cookies = [
                ('Set-Cookie', '%s=%s; Path=/; %s%s' % (
                    self.cookie_name, value, max_age, secure))
            ]
        else:
            cur_domain = environ.get('adhocracy.domain').split(':')[0]
            wild_domain = '.' + cur_domain

            cookies = [
                ('Set-Cookie', '%s=%s; Path=/; Domain=%s%s%s' % (
                    self.cookie_name, value, wild_domain, max_age, secure))
            ]
        return cookies
