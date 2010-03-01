import logging
         
from index import get_index, schema, ix_lock
from adhocracy.model import refs
from whoosh.qparser import MultifieldParser
from whoosh.query import *

log = logging.getLogger(__name__)

def run(terms, instance=None, entity_type=None, limit=100, 
        fields=[u'title', u'text', u'user', u'tags']):
    ix_lock.acquire()
    try:
        if terms is None:
            terms = u"?"
        searcher = get_index().searcher()    
        mparser = MultifieldParser(fields, schema=schema)
        query = mparser.parse(terms)
        
        if entity_type:
            query = Require(query, Term(u'doc_type', refs.entity_type(entity_type)))
        
        if instance:
            query = Require(query, Term(u'instance', instance.key))
        
        log.debug("Query: %s" % query)
        
        results = searcher.search(query, limit=limit)
        
        if entity_type is not None and hasattr(entity_type, 'find_all') and len(results):
            return entity_type.find_all(map(lambda r: refs.to_id(fields.get('ref')), results))
        
        entities = []
        for fields in results:
            ref = fields.get('ref')
            entity = refs.to_entity(ref)
            entities.append(entity)
        return entities
    finally:
        ix_lock.release()