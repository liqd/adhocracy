import logging

from adhocracy.lib.search.index import get_sunburnt_connection
from adhocracy.model import refs

from pylons import tmpl_context as c


log = logging.getLogger(__name__)


def sunburnt_query(entity_type=None, instance=None, connection=None):
    '''
    return a pre configured sunburnt query object. If *entity_type*
    is given, return a query object preconfigured to only fetch
    documents from solr with a matching doc_type. if instance is
    given, only documents are returned that contain the index
    key.

    *entity_type*
        An indexed model class. Indexed classes are listed
        in :data:`adhocracy.lib.search.INDEXED_CLASSES`.
    *instance*
        A :class:`adhocracy.model.Instance` object
    *connection*
        An existing sunburnt connection. Mostly useful
        in tests.
    '''
    if connection == None:
        connection = get_sunburnt_connection()
    q = connection.query()
    if entity_type:
        q = q.filter(doc_type=refs.cls_type(entity_type))
    if instance and c.instance:
        q = q.filter(instance=instance.key)
    return q

query = sunburnt_query


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
    q = sunburnt_query(entity_type=entity_type,
                       instance=instance)

    for term in terms.split():
        if ':' in term:
            field, value = term.split(':')
            q = q.query(**{field.strip(): value.strip()})
        else:
            q = add_wildcard_query(q, 'text', term.strip())

    response = q.execute()

    refs_ = [doc['ref'] for doc in response.result.docs]
    if refs_:
        return refs.to_entities(refs_)
    else:
        return []
