from pylons import session as pylons_session

from session import Session


# Register the session in the current context under the key in this variable.
# Set to configured option under `_key_session` in `SessionMiddleware.__init__`
# And if not set in the Configuration this is the default:
session_key = "session"


class SessionMiddleware(object):
    _session = pylons_session

    def __init__(self, app, config, **kwargs):
        global session_key

        self._app = app
        self._config = config or {}
        session_key = self._config.get("adhocracy.session.key", session_key)

    def __call__(self, environ, start_response):
        session = Session(environ, self._config)

        # Copy Beaker behavior to register the session in the Session
        # StackedObjectProxy
        if environ.get('paste.registry'):
            if environ['paste.registry'].reglist:
                environ['paste.registry'].register(self._session, session)

        # Register the session in the current environment
        environ[session_key] = session

        def session_start_response(status, headers, exc_info=None):
            # Sets the cookie headers only when the session values itself has
            # changed.
            session.set_cookies_in(headers)
            return start_response(status, headers, exc_info)

        return self._app(environ, session_start_response)

