import logging

from lucene import Term, TermQuery, MultiFieldQueryParser, \
                   BooleanClause, BooleanQuery, Hit
                   
import entityrefs
import index

log = logging.getLogger(__name__)

def run(terms, instance=None, cls=None, fields=['label', 'description', 'user']):
    bquery = BooleanQuery()
        
    equery = TermQuery(Term("entity", "true"))
    bquery.add(BooleanClause(equery, BooleanClause.Occur.MUST))
    
    if instance:
        iquery = TermQuery(Term("instance", str(instance.key)))
        bquery.add(BooleanClause(iquery, BooleanClause.Occur.MUST))
        
    if cls:
        tquery = TermQuery(Term("type", entityrefs._index_name(cls)))
        bquery.add(BooleanClause(tquery, BooleanClause.Occur.MUST))
        
    mquery = MultiFieldQueryParser.parse(terms, fields, 
        [BooleanClause.Occur.SHOULD] * len(fields),
        index.get_analyzer())
    bquery.add(BooleanClause(mquery, BooleanClause.Occur.MUST))  
    
    log.debug("Entity query: %s" % bquery.toString().encode("ascii", "replace"))
    
    hits = index.query(bquery)
    
    results = []
    for hit in hits:
        hit = Hit.cast_(hit)
        ref = hit.getDocument().getField("ref").stringValue()
        entity = entityrefs.to_entity(ref)
        score = hit.getScore()
        
        if entity:
            results.append(entity)
            log.debug(" Result: %s (type: %s), score: %s" % (repr(entity), 
                                                             repr(entity.__class__), 
                                                             score))
    return results