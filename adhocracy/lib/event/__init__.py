import logging 
from datetime import datetime

from pylons import session, tmpl_context as c

from event import Event
import util
from util import objtoken, EventException
from types import *
import query as q
from rss import rss_feed

import adhocracy.model as model

log = logging.getLogger(__name__)

def emit(event, data, agent, time=None, scopes=[], topics=[]):
    if not time: 
        time = datetime.now()
    e = Event(event, data, agent, time, scopes=scopes, topics=topics)
    e.persist()
    log.debug("Event %s: %s" % (agent.name, unicode(e)))
    return e