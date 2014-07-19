from raven import Client
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler
from raven.middleware import Sentry

from adhocracy import config as aconfig
from adhocracy.lib import version


class SentryMiddleware(Sentry):
    """
    As raven.middleware.Sentry doesn't really do what we need, we build our
    own. It merely extends Sentry in order to reuse the get_http_context
    method.
    """

    def __init__(self, app, config):
        self.app = app

        dsn = aconfig.get('adhocracy.sentry.dsn', config=config)
        if not dsn:
            raise Exception(
                'Sentry misconfigured. Please add adhocracy.sentry.dsn '
                'to your adhocracy config.')

        self.client = Client(dsn)

        handler = SentryHandler(
            self.client, level=aconfig.get('adhocracy.sentry.loglevel'))
        setup_logging(handler)

    def __call__(self, environ, start_response):
        self.client.tags_context({'version': version.get_version()})
        self.client.http_context(self.get_http_context(environ))
        return self.app(environ, start_response)
