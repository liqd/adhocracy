try:
    from Cookie import SimpleCookie
except ImportError:
    from http.cookies import SimpleCookie

from adhocracy.lib.session.converter import SignedValueConverter
from datetime import datetime

import logging


log = logging.getLogger(__name__)

class Session(dict):
    """ Stores session specific values on the client site, secured or unsecured
        through the `_converter` provided on initialization.
        `_converter` must be an object that responds to `encode` and `decode`
        messages.

        Use the `adhocracy.session.secret` configuration option to set a
        secret. If omitted, the `_converter` is in charge to select a random
        one, if it needs one.

        Use the `adhocracy.domain` configuration option to set a cookie domain.
    """

    def __init__(self, environ, config, path=None, http_only=None,
            value_converter=SignedValueConverter):
        self._config = config
        self._environ = environ

        # Set rfc 2109 values that do not change over time
        if "adhocracy.session.lifetime" in self._config:
            self._max_age = abs(long(
                self._config.get("adhocracy.session.lifetime")))
        else:
            self._max_age = None
            log.debug("cookie_option: no max-age set".format(self.__class__))

        self._domain = self._config["adhocracy.domain"]
        # Strip port from IPv6
        if self._domain.count(":") > 1:
            self._domain = self._domain.split("]")[0][1:-2]
        # Strip port from IPv4
        elif self._domain.count(":") == 1:
            self._domain = self._domain.split(":")[0]
        log.debug("domain = \"{1}\"".format(self.__class__, self._domain))

        # Set cookie options from the request
        self._path = path
        self._http_only = http_only

        self._converter = value_converter(
                self._config.get("adhocracy.session.secret", ""))

        self._load_session_from_cookie()

    def __setitem__(self, key, value):
        """ Sets a value under a specific key in the session and an encoded
            version of the value in the `_cookie` `SimpleCookie` object.
            This behavior prevents desynchronizing between the session and the
            `_cookie` `SimpleCookie` object.
        """
        super(Session, self).__setitem__(key, value)
        self._cookie[key] = self._converter.encode(value)
        self._changed = True

        log.debug("set in session: {1} = {2}".format(self.__class__, key, value))
        log.debug("set in cookie: {1} = {2}".format(
            self.__class__, key,
            self._converter.encode(value)))

    def _load_cookie(self):
        """ Initialize a new cookie with the cookie values from the
            environment if any available, then check the expires
        """
        self._cookie = SimpleCookie(self._environ.get("HTTP_COOKIE"))

        if "expires" in self._cookie:
            if self._converter.decode(
                    self._cookie["expires"]) <= datetime.utcnow():
                self._cookie = None

        return self._cookie != None


    def _new_session(self):
        """ Initializes a new session with a new `SimpleCookie` object and
            sets the expire value for the session.
        """
        self._cookie = SimpleCookie()
        if self._max_age:
            self["expires"] = datetime.utcnow() + self._max_age

        self._changed = True

    def _load_session_from_cookie(self):
        """ Loads the session values from the environment, creates a new
            cookie, decodes the values and stores them in the session iteself
            for efficient access.

            If no cookie information is in the environment it creates a new
            session.
        """
        if self._load_cookie():
            for key in self._cookie:
                log.debug("load in session try: {0}".format(key))
                val = self._converter.decode(self._cookie[key].value)
                log.debug("load in session try: {0} = {1}".format(key, val))
                if val:
                    super(Session, self).__setitem__(key, val)
                    log.debug("set in session: {0} = {1}".format(key, val))
            self._changed = False
        else:
            self._new_session()

    def _cookie_options(self):
        """ Returns a hash with options for a cookie if they exist in the
            session.
        """
        options = {}
        if self._path:
            options["path"] = self._path

        if self._max_age:
            options["max-age"] = self._max_age

        if self._domain:
            options["domain"] = self._domain

        if self._http_only:
            options["httponly"] = self._http_only

        if "expires" in self:
            options["expires"] = self["expires"]

        return options if options != {} else None


    def set_cookies_in(self, headers):
        """ Extends the cookie values with the cookie options from
            `_cookie_options` and then sets the rfc2109 encoded values with
            the \"Set-Cookie:\" Header in the the provided headers object.
        """
        if self._changed:
            options = self._cookie_options()
            for key in self:
                if options:
                    self._cookie[key].update(options)

                headers.append(("Set-Cookie",
                        self._cookie[key].output(header="")))

            self._changed = False

    def save(self):
        """ The session does not need this function, because of the saving
            of session values is passed to the client through cookies.
        """
        pass

