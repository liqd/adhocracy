import datetime
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin, _now

class InstanceAuthTktCookiePlugin(AuthTktCookiePlugin):

    def _get_cookies(self, environ, value, max_age=None):
        if max_age is not None:
            later = _now() + datetime.timedelta(seconds=int(max_age))
            # Wdy, DD-Mon-YY HH:MM:SS GMT
            expires = later.strftime('%a, %d %b %Y %H:%M:%S')
            # the Expires header is *required* at least for IE7 (IE7 does
            # not respect Max-Age)
            max_age = "; Max-Age=%s; Expires=%s" % (max_age, expires)
        else:
            max_age = ''

        cur_domain = environ.get('adhocracy.domain').split(':', 1)[0]
        wild_domain = '.' + cur_domain
        cookies = [
            #('Set-Cookie', '%s="%s"; Path=/%s' % (
            #self.cookie_name, value, max_age)),
            #('Set-Cookie', '%s="%s"; Path=/; Domain=%s%s' % (
            #self.cookie_name, value, cur_domain, max_age)),
            ('Set-Cookie', '%s="%s"; Path=/; Domain=%s%s' % (
            self.cookie_name, value, wild_domain, max_age))
            ]
        return cookies