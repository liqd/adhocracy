import logging
from hashlib import sha1

from pylons import app_globals

log = logging.getLogger(__name__)

SEP = "|"


class NoneResult(object):
    pass


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
    except:
        pass
    try:
        rep = unicode(obj).encode('ascii', 'ignore')
    except:
        pass
    return _hash(rep)


def make_key(iden, args, kwargs):
    sig = iden[:200] + make_tag(args) + make_tag(kwargs)
    return sha1(sig).hexdigest()


def clear_tag(tag):
    try:
        entities = app_globals.cache.get(make_tag(tag))
        if entities:
            app_globals.cache.delete_multi(entities.split(SEP))
    except TypeError:
        pass  # when app_globals isn't there yet


def memoize(iden, time=0):
    try:
        from pylons import tmpl_context as c
        iden = c.instance.key + '.' + iden if c.instance else iden
    except:
        pass

    def memoize_fn(fn):
        from adhocracy.lib.cache.util import NoneResult

        def new_fn(*a, **kw):
            try:
                cache = app_globals.cache
            except TypeError:
                # Probably in tests
                cache = None
            if not cache:
                res = fn(*a, **kw)
            else:
                key = make_key(iden, a, kw)
                res = cache.get(key)
                if res is None:
                    res = fn(*a, **kw)
                    #print "Cache miss", key + iden
                    if res is None:
                        res = NoneResult
                    #print "Cache set:", key + iden
                    cache.set(key, res, time=time)
                    tag_fn(key, a, kw)
                #else:
                    #print "Cache hit", key + iden
                if res == NoneResult:
                    res = None
            return res
        return new_fn
    return memoize_fn
