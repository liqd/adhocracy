import logging 
import os, os.path, shutil
from pylons import config

from whoosh import index
from whoosh.fields import *

DEFAULT_INDEX_DIR = "%(here)s/data/index"

log = logging.getLogger(__name__)

schema = Schema(title=TEXT(stored=True),
                ref=ID(stored=True, unique=True),
                doc_type=STORED,
                user=TEXT(stored=True),
                text=TEXT(stored=True),
                create_time=ID(stored=True),
                instance=ID(stored=True))

ix = None

def _index_dir():
    return config.get("adhocracy.index.dir", DEFAULT_INDEX_DIR % config)

def reset_index():
    global ix
    idir = _index_dir()
    log.warn("Resetting Whoosh index at: %s" % idir)
    if os.path.exists(idir):
        shutil.rmtree(idir)
    os.mkdir(idir)
    ix = index.create_in(idir, schema)
    
def open_index():
    global ix
    idir = _index_dir()
    if not os.path.exists(idir):
        reset_index()
    else:
        log.info("Opening Whoosh index at: %s" % idir)
        ix = index.open_dir(idir)
    
def get_index():
    global ix
    if not ix:
        open_index()
    return ix
    
    
    
    