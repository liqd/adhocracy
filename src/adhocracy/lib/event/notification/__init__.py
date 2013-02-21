import logging
from time import time
from itertools import chain

from sources import watchlist_source, vote_source, instance_source
from sources import delegation_source, tag_source, comment_source
from filters import self_filter, duplicates_filter, comment_filter
from sinks import log_sink, mail_sink, twitter_sink

log = logging.getLogger(__name__)


def echo(f):
    from pprint import pprint
    for x in f:
        pprint(x)
        yield x


def notify(event):
    '''
    been too smart today ;)
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

    pipeline = log_sink(pipeline)
    pipeline = twitter_sink(pipeline)
    pipeline = mail_sink(pipeline)

    for _ in pipeline:
        pass

    end_time = time() - begin_time
    log.debug("-> processing took: %sms" % (end_time * 1000))
