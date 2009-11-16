"""The application's Globals object"""
import logging

from pylons import config

from openid.store.memstore import MemoryStore
import memcache

from adhocracy import model
import cache
import search

log = logging.getLogger(__name__)

class Globals(object):

    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        if 'memcached.server' in config:
            self.cache = memcache.Client([config['memcached.server']])
            log.info("Memcache set up")
            self.cache.flush_all()
            cache.setup_cache()
        else:
            log.warn("Skipped memcache, no results caching will take place.")
            self.cache = None
        
        self.openid_store = MemoryStore()
        search.setup_search()
                
        