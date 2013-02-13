"""Pylons middleware initialization"""
from beaker.middleware import CacheMiddleware, SessionMiddleware
from fanstatic import Fanstatic
from paste.cascade import Cascade
from paste.registry import RegistryManager
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool
from pylons.middleware import ErrorHandler, StatusCodeRedirect
from pylons.wsgiapp import PylonsApp
from routes.middleware import RoutesMiddleware

from adhocracy.lib.auth.authentication import setup_auth
from adhocracy.lib.instance import setup_discriminator
from adhocracy.lib.machine_name import IncludeMachineName
from adhocracy.lib.util import get_site_path
from adhocracy.config.environment import load_environment
from adhocracy.lib.requestlog import RequestLogger
from adhocracy.lib.helpers.site_helper import base_url


def make_app(global_conf, full_stack=True, static_files=True, **app_conf):
    """Create a Pylons WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``full_stack``
        Whether this application provides a full WSGI stack (by default,
        meaning it handles its own exceptions and errors). Disable
        full_stack when this application is "managed" by another WSGI
        middleware.

    ``static_files``
        Whether this application serves its own static files; disable
        when another web server is responsible for serving them.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).

    """

    debug = (asbool(global_conf.get('debug', False)) or
             asbool(app_conf.get('debug', False)))

    # Configure the Pylons environment
    config = load_environment(global_conf, app_conf)

    # The Pylons WSGI app
    app = PylonsApp(config=config)

    # Routing/Session/Cache Middleware
    app = RoutesMiddleware(app, config['routes.map'])
    app = SessionMiddleware(app, config)
    app = CacheMiddleware(app, config)

    #app = make_profile_middleware(app, config, log_filename='profile.log.tmp')

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)
    app = setup_auth(app, config)
    app = setup_discriminator(app, config)
    if asbool(config.get('adhocracy.requestlog_active', 'False')):
        app = RequestLogger(app, config)

    if asbool(full_stack):
        # Handle Python exceptions
        app = ErrorHandler(app, global_conf, **config['pylons.errorware'])

    # Display error documents for 401, 403, 404 status codes
    app = StatusCodeRedirect(app, [400, 401, 403, 404, 500])

    # Establish the Registry for this application
    app = RegistryManager(app)

    if asbool(static_files):
        cache_age = int(config.get('adhocracy.static.age', 7200))
        # Serve static files
        overlay_app = StaticURLParser(
            get_site_path('static', app_conf=config),
            cache_max_age=None if debug else cache_age)
        static_app = StaticURLParser(
            config['pylons.paths']['static_files'],
            cache_max_age=None if debug else cache_age)
        app = Cascade([overlay_app, static_app, app])

    # Fanstatic inserts links for javascript and css ressources.
    # The required resources can be specified at runtime with <resource>.need()
    # and can will be delivered with version specifiers in the url and
    # minified when not in debug mode.
    fanstatic_base_url = base_url('', instance=None, config=config).rstrip('/')
    app = Fanstatic(app,
                    minified=not(debug),
                    versioning=True,
                    recompute_hashes=debug,
                    bundle=not(debug),
                    base_url=fanstatic_base_url,
                    bottom=True
                    )

    if asbool(config.get('adhocracy.include_machine_name_in_header', 'false')):
        app = IncludeMachineName(app, config)

    app.config = config

    return app
