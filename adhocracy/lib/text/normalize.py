import urllib
from unicodedata import normalize, category


def chr_filter(ch): 
    """ Filter by unicode character category. """
    cat = category(ch)[0].upper()
    if cat in ['Z']:
        return '_' # replace spaces
    if cat in ['P']:
        return '' # remove punctuation
    return ch
    

def title2alias(title, pseudo='pg'):
    #title = urllib.unquote(title)
    title = unicode(title).strip()
    title = normalize('NFKC', title)
    title = u''.join([chr_filter(c) for c in title])
    if not len(title):
        return pseudo
    try:
        tint = int(title)
        return pseudo + tint
    except:
        return title