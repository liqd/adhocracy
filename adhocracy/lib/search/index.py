from threading import Lock

import lucene

store = None
_analyzer = None

index_lock = Lock()

def get_writer():
    return lucene.IndexWriter(store, get_analyzer())
    
def get_reader():
    return lucene.IndexReader.open(store)
    
def get_searcher():
    return lucene.IndexSearcher(store)

def write_document(doc):
    index_lock.acquire()
    try:
        writer = get_writer()
        writer.addDocument(doc)
        writer.optimize()
        writer.close()
    finally:
        index_lock.release()
    
def delete_document(term):
    index_lock.acquire()
    try:
        reader = get_reader()
        reader.deleteDocuments(term)
        reader.close()
    finally:
        index_lock.release()
    
def query(q):
    index_lock.acquire()
    try:
        return get_searcher().search(q)
    finally:
        index_lock.release()
    
def get_analyzer():
    global _analyzer 
    if not _analyzer:
        # TODO: obviously refine tokenization and shit 
        _analyzer = lucene.StandardAnalyzer()
    return _analyzer
