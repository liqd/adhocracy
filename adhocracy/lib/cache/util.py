import logging
from base64 import b64encode
from hashlib import sha1

from pylons import g

class NoneResult(object): pass

log = logging.getLogger(__name__)

SEP="|"

cacheTags = {}

def add_tags(key, tags):
    ctags = g.cache.get_multi(tags)
    for tag in tags:
        if not ctags.get(tag):
            ctags[tag] = key
        else: 
            ctags[tag] += SEP + key
    g.cache.set_multi(ctags)
    
def tag_fn(key, a, kw):
    tags = []
    for arg in a:
        tags = tags + [arg]
    for kword in kw.values():
        tags = tags + [kword]
    add_tags(key, map(make_tag, tags))

def make_tag(obj):
    return make_key("__tag_", [obj], {})

def make_key(iden, a, kw=None):
    strs = map(str, a) + map(str, kw.items())
    #iden = "None" if iden is None else iden
    sig = sha1(b64encode(reduce(lambda s, p: s + p, strs, ""))).hexdigest()
    return iden[:210] + sig

def clear_tag(tag):
    try:
        tag = make_tag(tag)
        entities = g.cache.get(tag)
        if entities:
            g.cache.delete_multi(entities.split(SEP))
    except TypeError, te:
        pass
        #log.warn(te)

def memoize(iden, time = 0):
    def memoize_fn(fn):
        from adhocracy.lib.cache.util import NoneResult
        def new_fn(*a, **kw):
            if not g.cache:
                res = fn(*a, **kw)
            else:
                key = make_key(iden, a, kw)
                res = g.cache.get(key)
                if res is None:
                    res = fn(*a, **kw)
                    #print "Cache miss", key
                    if res is None:
                        res = NoneResult
                    #print "Cache set:", key
                    g.cache.set(key, res, time = time)
                    tag_fn(key, a, kw)
                #else:
                    #print "Cache hit", key
                if res == NoneResult:
                    res = None
            return res
        return new_fn
    return memoize_fn