import logging 


import adhocracy.model as model
import adhocracy.model.hooks as hooks

from index import open_index, reset_index, get_index
import query
from indexers import * 

log = logging.getLogger(__name__)

def setup_search():
    open_index()
    register_indexer(model.Category, index_category)
    register_indexer(model.Issue, index_issue)
    register_indexer(model.Motion, index_motion)
    register_indexer(model.User, index_user)
    register_indexer(model.Comment, index_comment)
    
    
def rebuild():
    reset_index()
    def index_all(iter, func):
        _insert = insert(func)
        [_insert(x) for x in iter]
    log.info("Re-indexing categories...")
    index_all(model.meta.Session.query(model.Category), index_category)
    log.info("Re-indexing issues...")
    index_all(model.meta.Session.query(model.Issue), index_issue)
    log.info("Re-indexing motions...")
    index_all(model.meta.Session.query(model.Motion), index_motion)
    log.info("Re-indexing users...")
    index_all(model.meta.Session.query(model.User), index_user)
    log.info("Re-indexing comments...")
    index_all(model.meta.Session.query(model.Comment), index_comment)
    log.info("... done")
    
        
        
            
    