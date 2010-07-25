import logging
from binascii import crc32
from hashlib import sha1

from pylons import app_globals

class NoneResult(object): pass

log = logging.getLogger(__name__)

SEP="|"

cacheTags = {}

def add_tags(key, tags):
    ctags = app_globals.cache.get_multi(tags)
    if not isinstance(ctags, type([])):
        ctags = {}
    for tag in tags:
        if not ctags.get(tag):
            ctags[tag] = str(key)
        else: 
            ctags[tag] += SEP + str(key)
    app_globals.cache.set_multi(ctags)
    
def tag_fn(key, a, kw):
    tags = []
    for arg in a:
        tags = tags + [arg]
    for kword in kw.values():
        tags = tags + [kword]
    add_tags(key, map(make_tag, tags))

def make_tag(obj):
    """ Collisisons here don't matter much. """
    try:    
        return str(hash(obj))
    except: pass
    try:
        return str(crc32(repr(obj)))
    except: pass
    return str(crc32(unicode(obj)))

def make_key(iden, args, kwargs=None):
    sig = unicode(iden[:200])
    sig += u"".join([make_tag(a) for a in args])
    sig += u"".join([make_tag(v) for k, v in kwargs.items()])
    return sha1(sig).hexdigest()

def clear_tag(tag):
    try:
        entities = app_globals.cache.get(make_tag(tag))
        if entities:
            app_globals.cache.delete_multi(entities.split(SEP))
    except TypeError, te:
        pass

def memoize(iden, time = 0):
    def memoize_fn(fn):
        from adhocracy.lib.cache.util import NoneResult
        def new_fn(*a, **kw):
            if not app_globals.cache:
                res = fn(*a, **kw)
            else:
                key = make_key(iden, a, kw)
                res = app_globals.cache.get(key)
                if res is None:
                    res = fn(*a, **kw)
                    #print "Cache miss", key
                    if res is None:
                        res = NoneResult
                    #print "Cache set:", key
                    app_globals.cache.set(key, res, time = time)
                    tag_fn(key, a, kw)
                #else:
                    #print "Cache hit", key
                if res == NoneResult:
                    res = None
            return res
        return new_fn
    return memoize_fn
