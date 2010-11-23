import logging
         
from index import get_connection
from adhocracy.model import refs

log = logging.getLogger(__name__)

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
        
        if entity_type is not None and hasattr(entity_type, 'find_all') and len(data.results):
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
