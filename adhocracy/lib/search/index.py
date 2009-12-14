from threading import Lock

import lucene

store = None
_analyzer = None


def get_writer():
    return lucene.IndexWriter(store, get_analyzer())
    
def get_reader():
    return lucene.IndexReader.open(store)
    
def get_searcher():
    return lucene.IndexSearcher(store)

def write_document(doc):
    writer = get_writer()
    writer.addDocument(doc)
    writer.optimize()
    writer.close()
    
def delete_document(term):
    reader = get_reader()
    reader.deleteDocuments(term)
    reader.close()
    
def query(q):
    return get_searcher().search(q)
    
def get_analyzer():
    global _analyzer 
    if not _analyzer:
        # TODO: obviously refine tokenization and shit 
        _analyzer = lucene.StandardAnalyzer()
    return _analyzer
