import logging 
from datetime import datetime

from pylons import session, tmpl_context as c

from types import *
import formatting
from rss import rss_feed
import notification
from .. import queue
from stats import *
from time import sleep 

import adhocracy.model as model

log = logging.getLogger(__name__)

SERVICE = 'event'

def emit(event, user, instance=None, topics=[], **kwargs):
    event = model.Event(event, user, kwargs, instance=instance)
    event.topics = topics
    model.meta.Session.add(event)
    model.meta.Session.commit()
    
    if queue.has_queue():
        queue.post_message(SERVICE, str(event.id))
    else:
        log.warn("Queue failure.")
        process(event)
     
    log.debug("Event: %s %s" % (user.user_name, formatting.as_unicode(event)))
    return event

def process(event):
    notification.notify(event)

def handle_queue_message(message):
    event = model.Event.find(int(message), instance_filter=False)
    process(event)
