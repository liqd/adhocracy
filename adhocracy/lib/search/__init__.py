'''Integrate solr with adhocracy'''

import logging

from adhocracy import model
from adhocracy.lib.search import index
from adhocracy.lib.search import query
from adhocracy.model import hooks


log = logging.getLogger(__name__)


INDEXED_CLASSES = (model.Proposal, model.Instance, model.User,
                   model.Comment, model.Page)


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


def rebuild_all():
    '''(re)index all indexable models in solr. This does not drop
    orphaned entries from the solr index.

    todo: add an option to clear the index before updating it.
    '''
    for cls in INDEXED_CLASSES:
        log.info("Re-indexing %ss..." % cls.__name__)
        for entity in model.meta.Session.query(cls):
            index.update(entity)
