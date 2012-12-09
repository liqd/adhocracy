from datetime import datetime, timedelta
import logging
import math

from adhocracy import model
from adhocracy.lib.cache import memoize
from adhocracy.lib.util import timedelta2seconds

log = logging.getLogger(__name__)


def activity(query_filter, from_time=None, to_time=None):
    if not to_time:
        to_time = datetime.utcnow()
    if not from_time:
        from_time = to_time - timedelta(days=30)
    base_age = timedelta2seconds(to_time - from_time)

    query = model.meta.Session.query(model.Event.time)
    query = query.filter(model.Event.time >= from_time)
    query = query.filter(model.Event.time <= to_time)
    query = query.order_by(model.Event.time.asc())
    query = query_filter(query)

    def evt_value(event_time):
        age = base_age - timedelta2seconds(to_time - event_time)
        return math.log(max(1, age))

    act = sum([evt_value(row[0]) for row in query])
    return act


@memoize('instance_activity', 86400)
def instance_activity(instance, from_time=None, to_time=None):
    def query_filter(q):
        return q.filter(model.Event.instance == instance)
    return activity(query_filter, from_time, to_time)


@memoize('user_activity', 86400)
def user_activity(instance, user, from_time=None, to_time=None):
    '''
    compute the user activity, either for a given
    :class:`adhocracy.model.Instance` *instance*, or across
    all instances if *instance* is `None`
    '''
    def query_filter(q):
        q = q.filter(model.Event.user == user)
        if instance is not None:
            q = q.filter(model.Event.instance == instance)
        return q
    return activity(query_filter, from_time, to_time)
