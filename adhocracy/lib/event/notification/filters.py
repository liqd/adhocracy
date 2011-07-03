from adhocracy.lib.event.types import (N_COMMENT_EDIT, N_COMMENT_REPLY,
                                       T_COMMENT_CREATE, T_COMMENT_EDIT)
from adhocracy.lib.event.notification.notification import Notification


def self_filter(pipeline):
    for notification in pipeline:
        if notification.type.notify_self:
            yield notification
        if not notification.event.user == notification.user:
            yield notification


def duplicates_filter(pipeline):
    recipient_map = {}
    for notification in pipeline:
        highest = recipient_map.get(notification.user)
        if (not highest) or (highest.priority <= notification.priority):
            recipient_map[notification.user] = notification
    for notification in recipient_map.values():
        yield notification


def _map_pipeline(mapper):
    def _mapping(pipeline):
        for notification in pipeline:
            r = mapper(notification)
            if r:
                yield r
            else:
                yield notification
    return _mapping


def _comment_mapper(n):
    if n.type == T_COMMENT_EDIT:
        for rev in n.event.comment.revisions:
            if rev.user == n.user:
                return Notification(n.event,
                                    n.user,
                                    type=N_COMMENT_EDIT,
                                    watch=n.watch)
    if n.type == T_COMMENT_CREATE:
        def check_parent(comment):
            for rev in comment.revisions:
                if rev.user == n.user:
                    return Notification(n.event,
                                        n.user,
                                        type=N_COMMENT_REPLY,
                                        watch=n.watch)
            if comment.reply:
                return check_parent(comment.reply)
        if n.event.comment.reply:
            return check_parent(n.event.comment.reply)

comment_filter = _map_pipeline(_comment_mapper)
