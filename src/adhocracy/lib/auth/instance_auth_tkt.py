from adhocracy.lib.cookie import get_cookies
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin


class InstanceAuthTktCookiePlugin(AuthTktCookiePlugin):
    def __init__(self, config, *args, **kwargs):
        super(InstanceAuthTktCookiePlugin, self).__init__(*args, **kwargs)
        self.__config = config

    def _get_cookies(self, environ, value, max_age=None):
        return get_cookies({self.cookie_name: value}, config=self.__config,
                           max_age=max_age, secure=self.secure)
