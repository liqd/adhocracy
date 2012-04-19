"""Pylons environment configuration"""
import os
import time
import traceback

from mako.lookup import TemplateLookup
from paste.deploy.converters import asbool
from pylons import config, tmpl_context as c
from pylons.error import handle_mako_error
from sqlalchemy import engine_from_config
from sqlalchemy.interfaces import ConnectionProxy

import adhocracy.lib.app_globals as app_globals
import adhocracy.lib.helpers
from adhocracy.config.routing import make_map
from adhocracy.model import init_model
from adhocracy.lib.search import init_search
from adhocracy.lib.democracy import init_democracy
from adhocracy.lib import init_site


def load_environment(global_conf, app_conf, with_db=True):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'static'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='adhocracy', paths=paths)

    config['routes.map'] = make_map()
    config['pylons.app_globals'] = app_globals.Globals()
    config['pylons.h'] = adhocracy.lib.helpers

    # Create the Mako TemplateLookup, with the default auto-escaping
    config['pylons.app_globals'].mako_lookup = TemplateLookup(
        directories=paths['templates'],
        error_handler=handle_mako_error,
        module_directory=os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding='utf-8', default_filters=['escape'],
        imports=['from webhelpers.html import escape'])

    # Setup the SQLAlchemy database engine
    connectionproxy = None
    if asbool(config.get('adhocracy.debug.sql', False)):
        connectionproxy = TimerProxy()
    engine = engine_from_config(config, 'sqlalchemy.', proxy=connectionproxy)
    init_model(engine)

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    init_site()
    if with_db:
        init_search()
    init_democracy()


class TimerProxy(ConnectionProxy):
    '''
    A timing proxy with code borrowed from spline and
    pyramid_debugtoolbar. This will work for sqlalchemy 0.6,
    but not 0.7. pyramid_debugtoolbar works for 0.7.
    '''

    def cursor_execute(self, execute, cursor, statement, parameters, context,
                       executemany):
        start_time = time.time()

        try:
            return execute(cursor, statement, parameters, context)
        finally:
            duration = time.time() - start_time

            # Find who spawned this query.  Rewind up the stack until we
            # escape from sqlalchemy code -- including this file, which
            # contains proxy stuff
            caller = '(unknown)'
            for frame_file, frame_line, frame_func, frame_code in \
                reversed(traceback.extract_stack()):

                if __file__.startswith(frame_file) \
                    or '/sqlalchemy/' in frame_file:

                    continue

                # OK, this is it
                caller = "{0}:{1} in {2}".format(
                    frame_file, frame_line, frame_func)
                break

            # save interesting information for presentation later
            try:
                if not c.pdtb_sqla_queries:
                    c.pdtb_sqla_queries = []
                queries = c.pdtb_sqla_queries
                query_data = {
                    'duration': duration,
                    'statement': statement,
                    'parameters': parameters,
                    'context': context,
                    'caller': caller,
                }
                queries.append(query_data)
            except TypeError:
                # happens when sql is emitted before pylons has started
                # or outside of a request
                pass
