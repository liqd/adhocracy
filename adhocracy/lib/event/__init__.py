import logging 
from datetime import datetime

from pylons import session, tmpl_context as c

from types import *
import formatting
from rss import rss_feed
import notification
import queue

import adhocracy.model as model

log = logging.getLogger(__name__)

def emit(event, user, instance=None, topics=[], **kwargs):
    #return
    event = model.Event(event, user, kwargs, instance=instance)
    event.topics = topics
    model.meta.Session.add(event)
    model.meta.Session.commit()
    model.meta.Session.refresh(event)
    
    if queue.has_queue():
        queue.post_event(event)
    else:
        log.warn("Queue failure.")
        process(event)
     
    log.debug("Event: %s %s" % (user.user_name, formatting.as_unicode(event)))
    return event

def process(event):
    notification.notify(event)

def queue_process():
    queue.read_events(process)
    


