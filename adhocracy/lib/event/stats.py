import logging
from datetime import datetime, timedelta

from adhocracy import model
from adhocracy.lib.cache import memoize
from adhocracy.lib.util import timedelta2seconds

import query

log = logging.getLogger(__name__)

BASE = datetime(2009, 8, 12, 13, 0, 0)

def activity(query_filter, from_time=None, to_time=None):    
    if not to_time:
        to_time = datetime.now()
    if not from_time:
        from_time = to_time - timedelta(days=30)
    
    query = model.meta.Session.query(model.Event.time)
    query = query.filter(model.Event.time >= from_time)
    query = query.filter(model.Event.time <= to_time)
    query = query.order_by(model.Event.time.asc())
    
    query = query_filter(query)
    
    def evt_value(time):
        t = max(1, timedelta2seconds(time - BASE))
        return 9001.0/float(t) # over 9000
    
    act = sum([evt_value(row[0]) for row in query])
    log.debug("Activity %s: %s" % (query, act))
    return act

@memoize('delegeteable_activity')
def delegateable_activity(dgb, from_time=None, to_time=None):
    def query_filter(q):
        return q.filter(model.Event.topics.contains(dgb))
    a = activity(query_filter, from_time, to_time)
    for child in dgb.children:
        a += delegateable_activity(child, from_time, to_time)
    return a

def motion_activity(motion, from_time=None, to_time=None):
    return delegateable_activity(motion, from_time, to_time)

def issue_activity(issue, from_time=None, to_time=None):
    return delegateable_activity(issue, from_time, to_time)

def category_activity(category, from_time=None, to_time=None):
    return delegateable_activity(category, from_time, to_time)

#@memoize('instance_activity')
def instance_activity(instance, from_time=None, to_time=None):
    def query_filter(q):
        return q.filter(model.Event.instance==instance)
    return activity(query_filter, from_time, to_time)

#@memoize('user_activity')
def user_activity(user, from_time=None, to_time=None):
    def query_filter(q):
        return q.filter(model.Event.user==user)
    return activity(query_filter, from_time, to_time)