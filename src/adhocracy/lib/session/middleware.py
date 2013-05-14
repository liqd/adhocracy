from pylons import session as pylons_session

from .session import Session


class CookieSessionMiddleware(object):
    def __init__(self, app, config):
        self._app = app
        self._config = config

    def __call__(self, environ, start_response):
        session = Session(environ, self._config)

        # Copy Beaker behavior to register the session in the Session
        # StackedObjectProxy
        if environ.get('paste.registry'):
            if environ['paste.registry'].reglist:
                environ['paste.registry'].register(pylons_session, session)

        environ['adhocracy_session'] = session

        def session_start_response(status, headers, exc_info=None):
            session.set_cookies_in(headers)
            return start_response(status, headers, exc_info)

        return self._app(environ, session_start_response)
