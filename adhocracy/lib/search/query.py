import logging
         
from index import get_index, schema, ix_lock
from adhocracy.model import refs
from whoosh.qparser import MultifieldParser
from whoosh.query import *

log = logging.getLogger(__name__)

def run(terms, instance=None, limit=50, fields=[u'title', u'text', u'user']):
    ix_lock.acquire()
    try:
        searcher = get_index().searcher()    
        mparser = MultifieldParser(fields, schema=schema)
        query = mparser.parse(terms)
        
        if instance:
            query = Require(query, Term(u'instance', instance.key))
        
        log.debug("Query: %s" % query)
        
        results = searcher.search(query, limit=limit)
        ix_lock.release()
        entities = []
        for fields in results:
            entity = refs.to_entity(fields.get('ref'))
            entities.append(entity)
        return entities
    except:
        ix_lock.release()
        raise