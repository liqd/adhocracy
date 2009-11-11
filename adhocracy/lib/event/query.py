import logging

from lucene import BooleanQuery, TermQuery, Term, Hit, BooleanClause, QueryParser

from event import Event
import util

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
    return "agent:%s" % util.objtoken(user)

def topic(obj):
    return "topic:%s" % util.objtoken(obj)

def scope(obj):
    return "scope:%s" % util.objtoken(obj)

def run(query, sort_time=True, sort_time_desc=True,
               from_time=None, to_time=None):
    import adhocracy.lib.search.index as index
    
    try:
        bquery = BooleanQuery()
        tquery = TermQuery(Term("type", "event"))
        bquery.add(BooleanClause(tquery, BooleanClause.Occur.MUST))
        if len(query.strip()):
            query = QueryParser("foo", index.get_analyzer()).parse(query)
            #log.debug("Compiled query: %s" % query.toString())
        else:
            query = TermQuery(Term("schnasel", "0xDEADBEEF"))
        bquery.add(BooleanClause(query, BooleanClause.Occur.MUST))
        
        log.debug("Event query: %s" % bquery)
    
        # TODO: run most of this in lucene, not here.
        hits = index.query(bquery)
        evts = []
        for hit in hits:
            hit = Hit.cast_(hit)
            evt = Event.restore(hit.getDocument())
            if evt:
                evts.append(evt)
        if from_time:
            evts = [e for e in evts if e.time >= from_time]
        if to_time:
            evts = [e for e in evts if e.time <= to_time]
        if sort_time:
            evts = sorted(evts, key=lambda e: e.time, reverse=sort_time_desc)
    except TypeError, e:
        log.warn(e)
        raise e
        return []
    return evts