import logging
from time import time
from itertools import chain

from adhocracy import config
from sources import watchlist_source, vote_source, instance_source
from sources import delegation_source, tag_source, comment_source
from filters import self_filter, duplicates_filter, comment_filter
from filters import hidden_instance_filter
from sinks import log_sink, mail_sink, twitter_sink
from sinks import database_sink

log = logging.getLogger(__name__)


def echo(f):
    from pprint import pprint
    for x in f:
        pprint(x)
        yield x


def notify(event, database_only=False):
    '''
    been too smart today ;)

    If database_only is True, the given event only creates Notfication
    database entries without sending out email and such notifications.
    '''
    if not event:
        log.warn("Received null as event, shouldn't happen!")
        return
    log.debug("Event notification processing: %s" % event)
    begin_time = time()
    sources = filter(lambda g: g, [watchlist_source(event),
                                   vote_source(event),
                                   instance_source(event),
                                   tag_source(event),
                                   delegation_source(event),
                                   comment_source(event)])
    pipeline = chain(*sources)
    #pipeline = echo(pipeline)

    pipeline = comment_filter(pipeline)
    pipeline = self_filter(pipeline)
    pipeline = duplicates_filter(pipeline)
    pipeline = hidden_instance_filter(pipeline)

    pipeline = log_sink(pipeline)
    if config.get_bool('adhocracy.store_notification_events'):
        pipeline = database_sink(pipeline)
    if not database_only:
        pipeline = twitter_sink(pipeline)
        pipeline = mail_sink(pipeline)

    for _ in pipeline:
        pass

    end_time = time() - begin_time
    log.debug("-> processing took: %sms" % (end_time * 1000))
