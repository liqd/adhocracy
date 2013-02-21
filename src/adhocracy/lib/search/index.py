import hashlib
import logging

from httplib2 import Http
from pylons import tmpl_context as c
from pylons import config
from sunburnt import SolrInterface

from adhocracy import model
from adhocracy.model import refs

log = logging.getLogger(__name__)
SKIP = 'skip'
ADD = 'add'
DELETE = 'delete'
IGNORE = 'ignore'


def get_sunburnt_connection():
    try:
        connection = c.sunburnt_connection
    except TypeError:
        # no tmpl_context. probably running in tests
        return make_connection()
    if not connection:
        c.sunburnt_connection = make_connection()
    return c.sunburnt_connection


def make_connection():
    solr_url = config.get('adhocracy.solr.url',
                          'http://localhost:8983/solr/')
    solr_url = solr_url.strip()
    if not solr_url.endswith('/'):
        solr_url = solr_url + '/'
    http_connection = Http()
    return SolrInterface(solr_url,
                         http_connection=http_connection)


def gen_id(entity):
    ref = refs.to_ref(entity)
    return hashlib.sha1(ref).hexdigest()


def update(entity):
    (action, data) = get_update_information(entity)
    if action == IGNORE:
        return

    connection = get_sunburnt_connection()
    try:
        if action == ADD:
            connection.add(data)
        elif action in (DELETE, SKIP):
            connection.delete(data)
        connection.commit()
    except Exception, e:
        log.exception(e)


def get_update_information(entity):
    if not isinstance(entity, model.meta.Indexable):
        return (IGNORE, None)
    if hasattr(entity, 'is_deleted') and entity.is_deleted():
        return (DELETE, gen_id(entity))
    data = entity.to_index()
    data['id'] = gen_id(entity)
    if data.pop('skip', False):
        return (SKIP, data['id'])
    return (ADD, data)


def delete(entity):
    connection = get_sunburnt_connection()
    try:
        index_id = gen_id(entity)
        connection.delete(index_id)
        connection.commit()
    except Exception, e:
        log.exception(e)
