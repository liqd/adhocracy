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
    log = logging.getLogger('')
    connection = index.get_sunburnt_connection()
    start = time.time()
    batch_start = time.time()
    done = 0
    other_classes = 0
    docs = {index.ADD: [],
            index.SKIP: [],
            index.DELETE: [],
            index.IGNORE: []}

    for cls in classes:
        if cls not in INDEXED_CLASSES:
            log.warn('Class "%s" is not an indexable class! skipping.' %
                     cls)
            continue
        log.info("Re-indexing %ss..." % cls.__name__)
        for entity in model.meta.Session.query(cls):
            (action, data) = index.get_update_information(entity)
            docs[action].append(data)
            done = done + 1
            if done % 1000 == 0:
                docs = commit_docs(docs, connection, log, start, batch_start)
                batch_start = time.time()
        log.info("...re-indexed %s %ss" % (done - other_classes, cls.__name__))
        other_classes = done
    commit_docs(docs, connection, log, start, batch_start)
    now = time.time()
    log.info('total: %s updates, %0.1f s' % (done, now - start))


def commit_docs(docs, connection, log, start, batch_start):
    to_add = docs[index.ADD]
    if len(to_add):
        connection.add(to_add)

    to_delete = docs[index.DELETE]
    if len(to_delete):
        connection.delete(to_delete)

    msg = "...indexed: %s/%s" % (len(to_add), len(to_delete))

    to_skip = docs[index.SKIP]
    if len(to_skip):
        connection.delete(to_skip)
        msg += ', skipped: %s' % len(to_skip)

    connection.commit()
    now = time.time()
    msg += ' in %0.1f s. Total time: %0.1f s' % (now - batch_start,
                                                 now - start)
    log.info(msg)
    for key in docs:
        docs[key] = []
    return docs


def rebuild_all():
    '''(re)index all indexable models in solr. This does not drop
    orphaned entries from the solr index.

    todo: add an option to clear the index before updating it.
    '''
    rebuild(INDEXED_CLASSES)
