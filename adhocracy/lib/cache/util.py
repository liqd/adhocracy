import logging
from binascii import crc32
from hashlib import sha1

from pylons import app_globals

class NoneResult(object): pass

log = logging.getLogger(__name__)

SEP="|"

cacheTags = {}

def _hash(data):
    return sha1(data).hexdigest()

def add_tags(key, tags):
    ctags = app_globals.cache.get_multi(tags)
    for tag in tags:
        if not ctags.get(tag):
            ctags[tag] = key
        else: 
            ctags[tag] = ctags[tag] + SEP + key
    app_globals.cache.set_multi(ctags)
    
def tag_fn(key, args, kwargs):
    tags = [make_tag(a) for a in args]
    tags += [make_tag(v) for v in kwargs.values()]
    add_tags(key, tags)

def make_tag(obj):
    """ Collisisons here don't matter much. """
    rep = "catch_all"
    try:
        rep = repr(obj).encode('ascii', 'ignore')
    except: pass
    try:
        rep = unicode(obj).encode('ascii', 'ignore')
    except: pass
    return _hash(rep)

def make_key(iden, args, kwargs):
    sig = iden[:200] + make_tag(args) + make_tag(kwargs)
    return sha1(sig).hexdigest()

def clear_tag(tag):
    entities = app_globals.cache.get(make_tag(tag))
    if entities:
        app_globals.cache.delete_multi(entities.split(SEP))
    
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
