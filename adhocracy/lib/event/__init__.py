import logging 
from datetime import datetime

from pylons import session, tmpl_context as c

from event import Event, EventException
from types import *
import query as q
from store import EventStore
from rss import rss_feed
import notification

import adhocracy.model as model

log = logging.getLogger(__name__)

def emit(event, agent, time=None, scopes=[], topics=[], **kwargs):
    e = Event(event, agent, time, scopes=scopes, topics=topics, **kwargs)
    es = EventStore(e)
    es.persist()
    #print "EVT ", e.to_json()
    log.debug("Event %s: %s" % (agent.name, unicode(e)))
    notification.notify(e)
    return e

