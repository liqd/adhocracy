import logging

from lucene import BooleanQuery, TermQuery, Term, BooleanClause, QueryParser, Version

from store import EventStore

log = logging.getLogger(__name__)

def _and(*pieces):
    if len(pieces) == 1:
        pieces = pieces[0]
    if isinstance(pieces, basestring):
        return pieces
    if not len(pieces):
        return ""
    return "(" + " AND ".join(pieces) + ")"

def _or(*pieces):
    if len(pieces) == 1:
        pieces = pieces[0]
    if isinstance(pieces, basestring):
        return pieces
    if not len(pieces):
        return ""
    return "(" + " OR ".join(pieces) + ")"

def _must(q):
    return "+" + q

def _not(q):
    return "-" + q

def agent(user):
    return "agent:%s" % EventStore.objtoken(user)

def topic(obj):
    return "topic:%s" % EventStore.objtoken(obj)

def scope(obj):
    return "scope:%s" % EventStore.objtoken(obj)

def run(query, sort_time=True, sort_time_desc=True,
               from_time=None, to_time=None, limit=1000):
    import adhocracy.lib.search.index as index

    bquery = BooleanQuery()
    tquery = TermQuery(Term("type", "event"))
    bquery.add(BooleanClause(tquery, BooleanClause.Occur.MUST))
    if len(query.strip()):
        query = QueryParser(Version.LUCENE_CURRENT, "foo", index.get_analyzer()).parse(query)
        #log.debug("Compiled query: %s" % query.toString())
    else:
        query = TermQuery(Term("schnasel", "0xDEADBEEF"))
    bquery.add(BooleanClause(query, BooleanClause.Occur.MUST))
    
    log.debug("Event query: %s" % bquery)

    # TODO: run most of this in lucene, not here.
    searcher = index.get_searcher()
    scoreDocs = searcher.search(bquery, limit).scoreDocs

    evts = []
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc).doc
        evt = EventStore._restore(doc)
        if evt:
            evts.append(evt)
    if from_time:
        evts = [e for e in evts if e.time >= from_time]
    if to_time:
        evts = [e for e in evts if e.time <= to_time]
    if sort_time:
        evts = sorted(evts, key=lambda e: e.time, reverse=sort_time_desc)
    return evts

