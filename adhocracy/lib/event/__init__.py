import logging 
from datetime import datetime
from threading import Lock

from pylons import session, tmpl_context as c

from event import Event, EventException
from types import *
import query as q
from store import EventStore
from rss import rss_feed
import notification
import queue

import adhocracy.model as model

log = logging.getLogger(__name__)
ep_lock = Lock()

def emit(event, agent, time=None, scopes=[], topics=[], **kwargs):
    e = Event(event, agent, time, scopes=scopes, topics=topics, **kwargs)
    es = EventStore(e)
    es.persist()
    
    if queue.has_queue():
        queue.post_event(e)
    else:
        log.warn("Queue failure.")
        process(e)
     
    log.debug("Event %s: %s" % (agent.name, unicode(e)))
    return e

def process(event):
    notification.notify(event)

def queue_process():
    available = ep_lock.acquire(blocking=False)
    if not available:
        return
    try:
        queue.read_events(process)
    finally:
        ep_lock.release()



