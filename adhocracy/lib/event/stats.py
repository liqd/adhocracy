import logging
import math
from datetime import datetime, timedelta
from time import time

from adhocracy import model
from adhocracy.lib.cache import memoize
from adhocracy.lib.util import timedelta2seconds

log = logging.getLogger(__name__)

def activity(query_filter, from_time=None, to_time=None):    
    if not to_time:
        to_time = datetime.utcnow()
    if not from_time:
        from_time = to_time - timedelta(days=30)
    
    query = model.meta.Session.query(model.Event.time)
    query = query.filter(model.Event.time >= from_time)
    query = query.filter(model.Event.time <= to_time)
    query = query.order_by(model.Event.time.asc())
    query = query_filter(query)
    
    base_age = timedelta2seconds(timedelta(days=7))
    now = datetime.utcnow()
        
    def evt_value(event_time):
        event_age = max(1, timedelta2seconds(now - event_time))
        relative_age = max(1, base_age - event_age)
        return math.log(relative_age)
    
    act = sum([evt_value(row[0]) for row in query])
    log.debug("Activity %s: %s" % (to_time, act))
    return act

@memoize('delegeteable_activity', 3600)
def delegateable_activity(dgb, from_time=None, to_time=None):
    def query_filter(q):
        return q.filter(model.Event.topics.contains(dgb))
    a = activity(query_filter, from_time, to_time)
    for child in dgb.children:
        a += delegateable_activity(child, from_time, to_time) 
    return a

def proposal_activity(proposal, from_time=None, to_time=None):
    return delegateable_activity(proposal, from_time, to_time)

def issue_activity(issue, from_time=None, to_time=None):
    return delegateable_activity(issue, from_time, to_time)

@memoize('instance_activity', 3600)
def instance_activity(instance, from_time=None, to_time=None):
    def query_filter(q):
        return q.filter(model.Event.instance==instance)
    return activity(query_filter, from_time, to_time)

@memoize('user_activity', 3600)
def user_activity(user, from_time=None, to_time=None):
    def query_filter(q):
        return q.filter(model.Event.user==user)
    return activity(query_filter, from_time, to_time)

def sparkline_samples(func, obj, step=timedelta(days=1), steps=60):
    begin_time = time = datetime.utcnow().date()
    samples = []
    for i in range(1, steps-1):
        offset = time - (step * i)
        samples.append(func(obj, from_time=offset-step, to_time=offset))
    return list(reversed(samples))
    

