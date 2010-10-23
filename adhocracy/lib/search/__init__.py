import logging 

import adhocracy.model as model
import adhocracy.model.hooks as hooks
from index import *
import query

log = logging.getLogger(__name__)

INDEXED_CLASSES = (model.Proposal, model.Instance, model.User, 
                   model.Comment, model.Page)

def init_search(with_db=True):
    for cls in INDEXED_CLASSES:
        hooks.register_queue_callback(cls, hooks.POSTINSERT, 
                                      index.update)
        hooks.register_queue_callback(cls, hooks.POSTUPDATE, 
                                      index.update)
        hooks.register_queue_callback(cls, hooks.PREDELETE, 
                                      index.delete)

def rebuild_all():
    clear()
    for cls in INDEXED_CLASSES:
        log.info("Re-indexing %ss..." % cls.__name__)
        for entity in model.meta.Session.query(cls):
            index.update(entity)
        
            
    