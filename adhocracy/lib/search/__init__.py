import logging 

from pylons import config

import lucene

import adhocracy.model as model
import adhocracy.model.hooks as hooks

import index
import query
from indexers import * 

DEFAULT_INDEX_DIR = "%(here)s/data/index"

log = logging.getLogger(__name__)

def index_dir():
    return config.get("lucene.index.dir", DEFAULT_INDEX_DIR % config)

def setup_search():
    index.vm = lucene.initVM(lucene.CLASSPATH)
    index.store  = lucene.FSDirectory.getDirectory(index_dir())
    
    index.write_document(lucene.Document())
    
    log.info("Started pyLucene %s, index at %s" % (lucene.VERSION, index_dir()))
    
    register_indexer(model.Category, CategoryIndexer)
    register_indexer(model.Issue, IssueIndexer)
    register_indexer(model.Motion, MotionIndexer)
    register_indexer(model.User, UserIndexer)
    register_indexer(model.Comment, CommentIndexer)
    
    
def attach_thread():
    index.vm.attachCurrentThread()