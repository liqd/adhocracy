import unicodedata
import re

SPLIT_CHARS = " ,;"
SPLITTER = re.compile(r'[,;\s]*', re.U)

def tag_normalize(text):
    if not isinstance(text, unicode):
        text = unicode(text)
    text = unicodedata.normalize('NFKC', text)
    return text.strip(SPLIT_CHARS)
    
def tag_split(text):
    tags = SPLITTER.split(text)
    return set(filter(len, tags))