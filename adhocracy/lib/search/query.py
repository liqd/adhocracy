import logging
         
from index import get_index, schema
from adhocracy.model import refs
from whoosh.qparser import MultifieldParser
from whoosh.query import *

log = logging.getLogger(__name__)

def run(terms, instance=None, entity_type=None, fields=[u'title', u'text', u'user', u'tags'], **kwargs):
    try:
        if terms is None:
            terms = u"?"
        searcher = get_index().searcher()    
        mparser = MultifieldParser(fields, schema=schema)
        query = mparser.parse(terms)
        
        if entity_type:
            query = Require(query, Term(u'doc_type', refs.cls_type(entity_type)))
        
        if instance:
            query = Require(query, Term(u'instance', instance.key))
        
        log.debug("Query: %s" % query)
        
        results = searcher.search(query)
        
        if entity_type is not None and hasattr(entity_type, 'find_all') and len(results):
            ids = [refs.to_id(r.get('ref')) for r in results]
            return entity_type.find_all(ids, **kwargs)
        
        entities = []
        for fields in results:
            ref = fields.get('ref')
            entity = refs.to_entity(ref, **kwargs)
            entities.append(entity)
        return entities
    except Exception, e:
        log.exception(e)
        return []
    finally:
        pass