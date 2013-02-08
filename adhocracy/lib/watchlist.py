import logging
import urllib

from pylons import tmpl_context as c, request

from adhocracy.model import meta, Watch, Comment, Delegateable
import adhocracy.model.refs as refs


log = logging.getLogger(__name__)


def find_watch(entity):
    return Watch.find_by_entity(c.user, entity)


def make_watch(entity):
    return urllib.urlencode({'ref': refs.to_url(entity)})


def check_watch(entity):
    if not c.user:
        return None
    watch = Watch.find_by_entity(c.user, entity)
    if request.params.get('watch') and not watch:
        Watch.create(c.user, entity)
    elif watch:
        watch.delete()
    meta.Session.commit()


def clean_stale_watches():
    log.debug("Beginning to clean up watchlist entries...")
    count = 0
    print count
    for watch in Watch.all():
        if hasattr(watch.entity, 'is_deleted') and \
                watch.entity.is_deleted():
            count += 1
            print count
            watch.delete()
    meta.Session.commit()
    if count > 0:
        log.debug("Removed %d stale watchlist entries." % count)


def traverse_watchlist(entity):
    """
    Traverse the watchlist for all affected topics. Returns only
    the most closely matching watchlist entries.
    """

    def merge(outer, inner):
        return inner + [w for w in outer if
                        not w.user in [w.user for w in inner]]

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
