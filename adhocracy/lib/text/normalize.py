from unicodedata import normalize, category
from adhocracy.forms import FORBIDDEN_NAMES


def chr_filter(ch, remove_space):
    """ Filter by unicode character category. """
    if ch == u'_':
        return ch
    cat = category(ch)[0].upper()
    if cat in ['Z'] and remove_space:
        return u'_'  # replace spaces
    if cat in ['P']:
        return u''  # remove punctuation
    return ch


def variant_normalize(variant, remove_space=False):
    var = escape(variant, remove_space=remove_space)
    return var


def title2alias(title, pseudo=u'page_'):
    #title = urllib.unquote(title)
    title = escape(title)
    #title = INVALID_CHARS.sub(u"", title)
    if (not len(title)) or (title.lower() in FORBIDDEN_NAMES):
        return pseudo
    try:
        tint = int(title)
        return pseudo + tint
    except:
        return title


def label2url(label):
    title = escape(label)
    return title[:40].encode('utf-8')


def simple_form(text):
    text = normalize('NFKC', text)
    return text


def escape(title, remove_space=True):
    if title is None:
        return None
    title = unicode(title).strip()
    title = normalize('NFKD', title)
    title = u''.join([chr_filter(c, remove_space) for c in title])
    title = normalize('NFKC', title)
    return title
