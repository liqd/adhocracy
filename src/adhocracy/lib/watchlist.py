import logging

from pylons import tmpl_context as c

from adhocracy.model import meta, Watch, Comment, Delegateable
import adhocracy.model.refs as refs


log = logging.getLogger(__name__)


def find_watch(entity):
    return Watch.find_by_entity(c.user, entity)


def make_watch(entity):
    return refs.to_url(entity)


def set_watch(entity, set_watch=True):
    """
    Make sure that the current user watches entity, if set_watch is True. Make
    sure that the current user doesn't watch entity, if set_watch is False.
    """
    has_watch = Watch.find_by_entity(c.user, entity)
    if set_watch and has_watch is None:
        Watch.create(c.user, entity)
        meta.Session.commit()
    elif not set_watch and has_watch is not None:
        has_watch.delete()
        meta.Session.commit()


def clean_stale_watches():
    log.debug("Beginning to clean up watchlist entries...")
    count = 0
    for watch in Watch.all():
        if hasattr(watch.entity, 'is_deleted') and \
                watch.entity.is_deleted():
            count += 1
            watch.delete()
    meta.Session.commit()
    if count > 0:
        log.debug("Removed %d stale watchlist entries." % count)


def traverse_watchlist(entity):
    """
    Traverse the watchlist for all affected topics. Returns only
    the most closely matching watchlist entries.
    """

    def merge(inner, outer):
        return inner + [w for w in outer if
                        w.user not in [ww.user for ww in inner]]

    watches = Watch.all_by_entity(entity)

    if isinstance(entity, Comment):
        if entity.reply is not None:
            watches = merge(watches,
                            traverse_watchlist(entity.reply))
        else:
            watches = merge(watches,
                            traverse_watchlist(entity.topic))
    elif isinstance(entity, Delegateable):
        if entity.milestone is not None and not entity.milestone.is_deleted():
            watches = merge(watches, traverse_watchlist(entity.milestone))
        if len(entity.parents):
            for parent in entity.parents:
                watches = merge(watches,
                                traverse_watchlist(parent))
        else:
            watches = merge(watches,
                            traverse_watchlist(entity.instance))
    return watches
