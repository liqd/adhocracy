import logging

from adhocracy import model
from adhocracy.lib.queue import async
from adhocracy.lib.event import formatting, notification
from adhocracy.lib.event.rss import rss_feed

from adhocracy.lib.event.types import EventType, NotificationType, TYPES
from adhocracy.lib.event.types import (
    T_USER_CREATE, T_USER_EDIT, T_USER_ADMIN_EDIT,
    T_INSTANCE_CREATE, T_INSTANCE_EDIT, T_INSTANCE_DELETE, T_INSTANCE_JOIN,
    T_INSTANCE_LEAVE, T_INSTANCE_FORCE_LEAVE, T_INSTANCE_MEMBERSHIP_UPDATE,
    T_PROPOSAL_CREATE, T_PROPOSAL_EDIT, T_PROPOSAL_STATE_REDRAFT,
    T_PROPOSAL_STATE_VOTING, T_PROPOSAL_DELETE,

    T_PAGE_CREATE, T_PAGE_EDIT, T_PAGE_DELETE,
    T_COMMENT_CREATE, T_COMMENT_EDIT, T_COMMENT_DELETE,
    T_DELEGATION_CREATE, T_DELEGATION_REVOKE,
    T_VOTE_CAST, T_RATING_CAST, T_SELECT_VARIANT, T_TEST,

    N_DELEGATION_RECEIVED, N_DELEGATION_LOST,
    N_INSTANCE_FORCE_LEAVE, N_INSTANCE_MEMBERSHIP_UPDATE,
    N_SELF_VOTED, N_DELEGATE_VOTED, N_DELEGATE_CONFLICT,
    N_COMMENT_REPLY, N_COMMENT_EDIT)


log = logging.getLogger(__name__)


def emit(event, user, instance=None, topics=[], **kwargs):
    event = model.Event(event, user, kwargs, instance=instance)
    event.topics = topics
    model.meta.Session.add(event)
    model.meta.Session.commit()

    handle_queue_message(str(event.id))
    log.debug("Event: %s %s, data: %r" % (user.user_name, event, event.data))
    return event


def process(event):
    notification.notify(event)


@async
def handle_queue_message(message):
    event = model.Event.find(int(message), instance_filter=False)
    process(event)


# The funny thing about this line is: YOU DO NOT SEE IT!
TYPES = filter(lambda n: isinstance(n, NotificationType), map(eval, dir()))
