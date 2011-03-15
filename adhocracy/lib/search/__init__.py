'''Integrate solr with adhocracy'''

import logging

from adhocracy import model
from adhocracy.lib.search import index
from adhocracy.lib.search import query
from adhocracy.model import hooks


log = logging.getLogger(__name__)


INDEXED_CLASSES = (model.Proposal, model.Instance, model.User,
                   model.Comment, model.Page)


def init_search(with_db=True):
    '''Register callback functions for commit hooks to add/update and
    delete documents in solr when model instances are commited.
    '''

    for cls in INDEXED_CLASSES:
        hooks.register_queue_callback(cls, hooks.POSTINSERT,
                                      index.update)
        hooks.register_queue_callback(cls, hooks.POSTUPDATE,
                                      index.update)
        hooks.register_queue_callback(cls, hooks.PREDELETE,
                                      index.delete)


def rebuild_all():
    '''(re)index all indexable models in solr. This does not drop
    orphaned entries from the solr index.

    todo: add an option to clear the index before updating it.
    '''
    for cls in INDEXED_CLASSES:
        log.info("Re-indexing %ss..." % cls.__name__)
        for entity in model.meta.Session.query(cls):
            index.update(entity)
