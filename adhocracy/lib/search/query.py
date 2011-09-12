import logging

from httplib2 import Http
from sunburnt import SolrInterface

from adhocracy.lib.search.index import get_connection
from adhocracy.model import refs

log = logging.getLogger(__name__)


def get_sunburnt_connection():
    from pylons import config
    solr_url = config.get('adhocracy.solr.url', 'http://localhost:8983/solr/')
    solr_url = solr_url.strip()
    if not solr_url.endswith('/'):
        solr_url = solr_url + '/'
    http_connection = Http()

    return SolrInterface(solr_url, http_connection=http_connection,
                         mode='r')


def sunburnt_query(entity_type=None):
    '''
    return a sunburnt query object. If *entity_type* is given,
    return a query object preconfigured to only fetch documents
    from solr with a matching doc_type
    '''
    si = get_sunburnt_connection()
    q = si.query()
    if entity_type:
        q = q.filter(doc_type=refs.cls_type(entity_type))
    return q


def add_wildcard_query(query, field, string, lower=True):
    '''
    add a wildcard search for all words in *string* for the solr
    *field* to the existing sunburnt *query*.

    *query*
       :class:`sunburnt.search.SolrSearch` query object
    *field*
       `str`. The name of the solr field.
    *string*
       `str` or `unicode`. The search terms as a string
    *lower*
       `boolean`. If True (default) the search terms will be lowercased.
       This is required if the search index is lowercased, which it
       probably will be.

    Returns: A :class:`sunburnt.search.SolrSearch` object
    '''
    if string is None:
        return query

    if lower:
        string = string.lower()

    for term in string.split():
        term = term.strip('*')

        # We need to search for both the term or the term
        # with an wildcard.
        term_query = query.Q(**{field: term}) | query.Q(**{field: term + '*'})

        # chain this with the rest of the query as an AND query
        query = query.query(term_query)
    return query


def run(terms, instance=None, entity_type=None, **kwargs):
    conn = get_connection()
    try:
        if terms is None or not len(terms):
            terms = u'*:*'

        filter_query = u''

        if entity_type:
            filter_query += u'+doc_type:%s' % refs.cls_type(entity_type)

        if instance:
            filter_query += u' +instance:%s' % instance.key

        log.debug("Query: %s (fq: %s)" % (terms, filter_query))
        data = conn.query(terms, fq=filter_query, rows=1000)

        if (entity_type is not None and hasattr(entity_type, 'find_all') and
            len(data.results)):
            ids = [refs.to_id(r.get('ref')) for r in data.results]
            return entity_type.find_all(ids, **kwargs)

        entities = []
        for fields in data.results:
            ref = fields.get('ref')
            entity = refs.to_entity(ref, **kwargs)
            entities.append(entity)
        return entities
    except Exception, e:
        log.exception(e)
        return []
    finally:
        conn.close()
