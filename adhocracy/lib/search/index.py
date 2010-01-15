import logging 
import os, os.path, shutil
from threading import Lock 

from whoosh import index
from whoosh.fields import *

log = logging.getLogger(__name__)

schema = Schema(title=TEXT(stored=True),
                ref=ID(stored=True, unique=True),
                doc_type=STORED,
                user=TEXT(stored=True),
                text=TEXT(stored=True),
                create_time=ID(stored=True),
                instance=ID(stored=True))

ix = None
ix_lock = Lock()

def create_index(index_dir):
    global ix
    ix_lock.acquire()
    try:
        ix = index.create_in(index_dir, schema)
    finally:
        ix_lock.release()
    
def open_index(index_dir):
    global ix
    ix_lock.acquire()
    try:
        ix = index.open_dir(index_dir)
    finally:
        ix_lock.release()
    
def get_index():
    global ix
    if ix is None:
        raise ValueError("Index is not open")
    return ix
    
    
    
    