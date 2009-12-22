import logging

from lucene import Term, TermQuery, MultiFieldQueryParser, \
                   BooleanClause, BooleanQuery, Version
                   
import entityrefs
import index

log = logging.getLogger(__name__)

def run(terms, instance=None, cls=None, limit=50, fields=['label', 'description', 'user']):
    bquery = BooleanQuery()
        
    equery = TermQuery(Term("entity", "true"))
    bquery.add(BooleanClause(equery, BooleanClause.Occur.MUST))
    
    if instance:
        iquery = TermQuery(Term("instance", str(instance.key)))
        bquery.add(BooleanClause(iquery, BooleanClause.Occur.MUST))
        
    if cls:
        tquery = TermQuery(Term("type", entityrefs._index_name(cls)))
        bquery.add(BooleanClause(tquery, BooleanClause.Occur.MUST))
        
    mquery = MultiFieldQueryParser.parse(Version.LUCENE_CURRENT,
        terms, fields, 
        [BooleanClause.Occur.SHOULD] * len(fields),
        index.get_analyzer())
    bquery.add(BooleanClause(mquery, BooleanClause.Occur.MUST))  
    
    log.debug("Entity query: %s" % bquery.toString().encode("ascii", "replace"))
    
    searcher = index.get_searcher()
    scoreDocs = searcher.search(bquery, limit).scoreDocs
    
    results = []
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        doc.getField("ref").stringValue()
        entity = entityrefs.to_entity(ref)
        
        if entity:
            results.append(entity)
    return results