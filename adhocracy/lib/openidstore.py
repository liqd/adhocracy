import logging

from openid.consumer.consumer import Consumer
from openid.store.sqlstore import MySQLStore, PostgreSQLStore, SQLiteStore
from pylons import config

from adhocracy.model import meta

SQL_STORES = {'sqlite': SQLiteStore,
              'mysql': MySQLStore,
              'postgres': PostgreSQLStore,
              'postgresql': PostgreSQLStore}

log = logging.getLogger(__name__)

store = None


def create_store():
    log.debug("Creating SQL-based OpenID store...")
    conn_str = config.get('sqlalchemy.url')
    if conn_str is None:
        raise ValueError("OpenID connection")
    db_type = conn_str.split(':')[0]
    store_cls = SQL_STORES.get(db_type)
    return store_cls(meta.engine.raw_connection())


def create_consumer(openid_session):
    global store
    if store is None:
        store = create_store()
    return Consumer(openid_session, store)
