'''Integrate solr with adhocracy'''

import logging
import time

from adhocracy import model
from adhocracy.lib.search import index


log = logging.getLogger(__name__)


INDEXED_CLASSES = (model.Proposal, model.Instance, model.User,
                   model.Comment, model.Page, model.Milestone)


def init_search():
    '''Register callback functions for commit hooks to add/update and
    delete documents in solr when model instances are commited.
    '''
    from adhocracy.lib.queue.update import LISTENERS
    from adhocracy.model.update import INSERT, UPDATE, DELETE
    for cls in INDEXED_CLASSES:
        LISTENERS[(cls, INSERT)].append(index.update)
        LISTENERS[(cls, UPDATE)].append(index.update)
        LISTENERS[(cls, DELETE)].append(index.delete)


def rebuild(classes):
    '''
    (Re)Index all entities of the given *classes*.
    '''
    start = time.time()
    done = 0
    connection = index.get_connection()
    for cls in classes:
        if cls not in INDEXED_CLASSES:
            log.warn('Class "%s" is not an indexable class! skipping.' %
                     cls)
            continue
        log.info("Re-indexing %ss..." % cls.__name__)
        for entity in model.meta.Session.query(cls):
            index.update(entity, connection=connection, commit=False)
            done = done + 1
            if done % 100 == 0:
                connection.commit()
                log.info('indexed %d in %ss' % (done, time.time() - start))
    connection.commit()
    connection.close()

def rebuild_all():
    '''(re)index all indexable models in solr. This does not drop
    orphaned entries from the solr index.

    todo: add an option to clear the index before updating it.
    '''
    rebuild(INDEXED_CLASSES)
