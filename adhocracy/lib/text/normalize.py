import urllib
from webhelpers.text import truncate
from unicodedata import normalize, category
from adhocracy.forms import FORBIDDEN_NAMES

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
    title = escape(title)
    if not len(title) or title.lower() in FORBIDDEN_NAMES:
        return pseudo
    try:
        tint = int(title)
        return pseudo + tint
    except:
        return title


def label2alias(label):
    title = escape(label)
    return title[:40]


def escape(title):
    title = unicode(title).strip()
    title = normalize('NFKD', title)
    title = u''.join([chr_filter(c) for c in title])
    title = normalize('NFKC', title)
    return title