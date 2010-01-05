import logging 
import os, os.path, shutil
from pylons import config
import adhocracy.model as model
import adhocracy.model.hooks as hooks

from index import open_index, create_index, get_index
import query
from indexers import * 

DEFAULT_INDEX_DIR = "%(here)s/data/index"

log = logging.getLogger(__name__)

def _index_dir():
    return config.get("adhocracy.index.dir", DEFAULT_INDEX_DIR % config)

def setup_search():
    init()
    register_indexer(model.Category, index_category)
    register_indexer(model.Issue, index_issue)
    register_indexer(model.Motion, index_motion)
    register_indexer(model.User, index_user)
    register_indexer(model.Comment, index_comment)

def init():
    index_dir = _index_dir()
    if not os.path.exists(index_dir):
        log.warn("Resetting Whoosh index at: %s" % index_dir)
        reset()
    else:
        log.info("Opening Whoosh index at: %s" % index_dir)
        open_index(index_dir)
        
def reset():
    index_dir = _index_dir()
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
    os.mkdir(index_dir)
    create_index(index_dir)
    #rebuild_all()
    
def rebuild_all():
    def index_all(iter, func):
        _insert = update(func)
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
    
        
        
            
    