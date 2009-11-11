import logging
from datetime import datetime

from adhocracy import model
from ..cache import memoize
from ..util import timedelta2seconds

import query

log = logging.getLogger(__name__)

BASE = datetime(2009, 8, 12, 13, 0, 0)

def activity(q, from_time=None, to_time=None):    
    events = query.run(q, from_time=from_time, to_time=to_time)
    events = reversed(events)
    
    if not to_time:
        to_time = datetime.now()
    if not from_time:
        from_time = datetime.min
        
    events = [e for e in events if e.time >= from_time \
              and e.time < to_time]
        
    def evt_value(e):
        t = max(1, timedelta2seconds(e.time - BASE))
        return 9001.0/float(t) # over 9000
    
    act = sum(map(evt_value, events))
    log.debug("Activity %s: %s" % (q, act))

    return act * -1

@memoize('motion_activity')
def motion_activity(motion, from_time=None, to_time=None):
    a = activity(query.topic(motion), from_time=from_time, to_time=to_time)
    return a

@memoize('issue_activity')
def issue_activity(issue, from_time=None, to_time=None):
    a = activity(query.topic(issue), from_time=from_time, to_time=to_time)
    a += sum(map(lambda m: motion_activity(m, from_time=from_time, to_time=to_time),
                 issue.motions))
    return a

@memoize('category_activity')
def category_activity(category, from_time=None, to_time=None):
    a = activity(query.topic(category), from_time=from_time, 
                 to_time=to_time)
    for child in category.children:
        if isinstance(child, model.Category):
            a += category_activity(child, from_time=from_time, 
                                   to_time=to_time)
        elif isinstance(child, model.Issue):
            a += issue_activity(child, from_time=from_time, 
                                   to_time=to_time)
    return a

@memoize('instance_activity')
def instance_activity(instance, from_time=None, to_time=None):
    a = activity(query.scope(instance), from_time=from_time, to_time=to_time)
    return a

@memoize('user_activity')
def user_activity(user, from_time=None, to_time=None):
    a = activity(query._or(query.topic(user), query.agent(user)), from_time=from_time, to_time=to_time)
    return a