import logging

from adhocracy import model
from adhocracy.lib import queue
from adhocracy.lib.event import formatting, notification
from adhocracy.lib.event.rss import rss_feed
from adhocracy.lib.event.stats import *
from adhocracy.lib.event.types import *

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

    log.debug("Event: %s %s, data: %r" % (user.user_name, event, event.data))
    return event


def process(event):
    notification.notify(event)


def handle_queue_message(message):
    event = model.Event.find(int(message), instance_filter=False)
    process(event)
