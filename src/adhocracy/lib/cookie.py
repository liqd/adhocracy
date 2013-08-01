import datetime
import re

from paste.deploy.converters import asbool
from pylons import config

# Valid cookie values, see http://tools.ietf.org/html/rfc6265#section-4.1.1
_COOKIE_VALUE_RE = re.compile(u'^[!#$%&\'()*+./0-9:<=>?@A-Z[\\]^_`a-z{|}~-]*$')


def get_cookies(values, max_age=None, secure=False, config=config):
    return [get_cookie(k, v, max_age=max_age, secure=secure, config=config)
            for k, v in values.items()]


def get_cookie(name, value, max_age=None, secure=False, config=config):
    assert _COOKIE_VALUE_RE.match(value)

    if max_age == 'delete':
        max_age = '; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
    elif max_age is not None:
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(seconds=int(max_age))
        # Wdy, DD-Mon-YY HH:MM:SS GMT
        expires = later.strftime('%a, %d %b %Y %H:%M:%S')
        # the Expires header is *required* at least for IE7 (IE7 does
        # not respect Max-Age)
        max_age = "; Max-Age=%s; Expires=%s" % (max_age, expires)
    else:
        max_age = ''

    secure_str = ''
    if secure:
        secure_str = '; secure'
    secure_str += '; HttpOnly'

    if asbool(config.get('adhocracy.relative_urls', 'false')):
        # Serve the cookie for the current host, which may be
        # "localhost" or an IP address.
        return ('Set-Cookie', '%s=%s; Path=/; %s%s' % (
                name, value, max_age, secure_str))
    else:
        cur_domain = config.get('adhocracy.domain').partition(':')[0]
        wild_domain = '.' + cur_domain

        return ('Set-Cookie', '%s=%s; Path=/; Domain=%s%s%s' % (
                name, value, wild_domain, max_age, secure_str))
