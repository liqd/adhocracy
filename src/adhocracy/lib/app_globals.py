"""The application's Globals object"""
import logging

import memcache


log = logging.getLogger(__name__)


class Globals(object):

    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self, config):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        if 'memcached.server' in config:
            self.cache = memcache.Client([config['memcached.server']])
            log.info("Memcache set up")
            log.debug("Flushing cache")
            self.cache.flush_all()
        else:
            log.warn("Skipped memcache, no results caching will take place.")
            self.cache = None

        if 'adhocracy.instance' in config:
            self.single_instance = config.get('adhocracy.instance')
        else:
            self.single_instance = None
