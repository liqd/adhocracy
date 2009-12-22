from threading import Lock

import lucene

store = None
_analyzer = None


def get_writer():
    writer = lucene.IndexWriter(store, get_analyzer(), True, 
                                lucene.IndexWriter.MaxFieldLength.LIMITED)
    writer.setMaxFieldLength(1048576)
    return writer
    
def get_reader():
    return lucene.IndexReader.open(store)
    
def get_searcher():
    return lucene.IndexSearcher(store, True)

def write_document(doc):
    writer = get_writer()
    writer.addDocument(doc)
    writer.optimize()
    writer.close()
    
def delete_document(term):
    reader = get_reader()
    reader.deleteDocuments(term)
    reader.close()
    
def get_analyzer():
    global _analyzer 
    if not _analyzer:
        # TODO: obviously refine tokenization and shit 
        _analyzer = lucene.StandardAnalyzer(lucene.Version.LUCENE_CURRENT)
    return _analyzer
