from adhocracy.lib.event.notification.notification import Notification
from adhocracy.lib import democracy, watchlist
from adhocracy.lib.event.types import (
    N_COMMENT_EDIT,
    N_DELEGATE_CONFLICT, N_DELEGATE_VOTED,
    N_DELEGATION_LOST, N_DELEGATION_RECEIVED,
    N_INSTANCE_FORCE_LEAVE, N_INSTANCE_MEMBERSHIP_UPDATE,
    N_SELF_VOTED,
    T_COMMENT_EDIT,
    T_DELEGATION_CREATE, T_DELEGATION_REVOKE,
    T_INSTANCE_FORCE_LEAVE, T_INSTANCE_MEMBERSHIP_UPDATE,
    T_RATING_CAST, T_SELECT_VARIANT, T_VOTE_CAST)


def watchlist_source(event):
    watches = watchlist.traverse_watchlist(event.user)
    for topic in event.topics:
        watches += watchlist.traverse_watchlist(topic)
    for watch in watches:
        yield Notification(event, watch.user, watch=watch)


def vote_source(event):
    """
    Notify users about their voting behaviour, especially about
    delegated votes.
    """
    if event.event in [T_VOTE_CAST, T_SELECT_VARIANT, T_RATING_CAST]:
        decision = democracy.Decision(event.user, event.poll)
        before = decision.without_vote(event.vote)
        if (map(lambda v: v.delegation, decision.relevant_votes) ==
            map(lambda v: v.delegation, before.relevant_votes)) and \
           (before.result == decision.result):
            return
        if not decision.is_decided():
            yield Notification(event, event.user, type=N_DELEGATE_CONFLICT)
        elif decision.is_self_decided():
            yield Notification(event, event.user, type=N_SELF_VOTED)
        else:
            yield Notification(event, event.user, type=N_DELEGATE_VOTED)


def delegation_source(event):
    """
    Notifiy users of gained and lost delegations.
    """
    if event.event == T_DELEGATION_CREATE:
        yield Notification(event, event.agent, type=N_DELEGATION_RECEIVED)
    elif event.event == T_DELEGATION_REVOKE:
        yield Notification(event, event.agent, type=N_DELEGATION_LOST)


def instance_source(event):
    """
    Notifiy users of changes in their instance membership.
    """
    if event.event == T_INSTANCE_FORCE_LEAVE:
        yield Notification(event, event.user,
                           type=N_INSTANCE_FORCE_LEAVE)
    elif event.event == T_INSTANCE_MEMBERSHIP_UPDATE:
        yield Notification(event, event.user,
                           type=N_INSTANCE_MEMBERSHIP_UPDATE)


def tag_source(event):
    watches = []
    for topic in event.topics:
        for (tag, count) in topic.tags:
            watches = watchlist.traverse_watchlist(tag)
    for watch in set(watches):
        yield Notification(event, watch.user, watch=watch)


def comment_source(event):
    if event.event == T_COMMENT_EDIT:
        for revision in event.comment.revisions:
            yield Notification(event,
                               revision.user,
                               type=N_COMMENT_EDIT)
    if 'comment' in event.data:
        for watch in watchlist.traverse_watchlist(event.comment):
            yield Notification(event, watch.user, watch=watch)
