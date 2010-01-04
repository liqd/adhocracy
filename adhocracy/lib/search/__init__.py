import logging 

from pylons import config

import adhocracy.model as model
import adhocracy.model.hooks as hooks

import index
import query
from indexers import * 

DEFAULT_INDEX_DIR = "%(here)s/data/index"

log = logging.getLogger(__name__)

def index_dir():
    return config.get("adhocracy.index.dir", DEFAULT_INDEX_DIR % config)

def setup_search():
    #register_indexer(model.Category, CategoryIndexer)
    #register_indexer(model.Issue, IssueIndexer)
    #register_indexer(model.Motion, MotionIndexer)
    #register_indexer(model.User, UserIndexer)
    #register_indexer(model.Comment, CommentIndexer)
    pass