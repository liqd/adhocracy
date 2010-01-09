import logging 

from pylons import config, g

from openid.consumer.consumer import Consumer
from openid.store.memstore import MemoryStore
from openid.store.filestore import FileOpenIDStore
from openid.store.sqlstore import MySQLStore, PostgreSQLStore, SQLiteStore

from adhocracy.model import meta

SQL_STORES = {'sqlite': SQLiteStore,
              'mysql': MySQLStore,
              'postgres': PostgreSQLStore}

log = logging.getLogger(__name__)

def _create_sql_store():
    log.debug("Creating SQL-based OpenID store...")
    conn_str = config.get('sqlalchemy.url')
    if conn_str is None: raise ValueError("OpenID connection")
    db_type = conn_str.split(':')[0]
    store_cls = SQL_STORES.get(db_type)  
    return store_cls(meta.engine.raw_connection())
    
def _create_file_store():
    log.debug("Creating FS-based OpenID store...")
    if 'cache_dir' not in config:
        raise KeyError() # yeah that could be achieved easier
    return FileOpenIDStore(config.get('cache_dir'))

def _create_store():
    # Say it loudly, say it proudly: WTF? 
    try:
        return _create_sql_store()
    except Exception, e:
        log.exception(e)
        try:
            return _create_file_store()
        except Exception, e:
            log.exception(e)
            return MemoryStore()
        
def create_consumer(openid_session):
    if not hasattr(g, 'openid_store'):
        g.openid_store = _create_store()
    return Consumer(openid_session, g.openid_store)