"""SQLAlchemy Metadata and Session object"""
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from decorator import decorator
import hooks

__all__ = ['Session', 'data', 'extension', 'engine']

# SQLAlchemy database engine.  Updated by model.init_model()
engine = None

# SQLAlchemy session manager.  Updated by model.init_model()
# REFACT: this is an instance, not a class - so it should be lowercased
Session = None

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
data = MetaData()

extension = hooks.HookExtension() 


#@decorator
#def session_cached(f, *a, **kw):
#    from adhocracy.lib.cache.util import make_key
#    cache = getattr(Session, '_unique_cache', None)
#    if cache is None:
#        Session._unique_cache = cache = {}
#
#    key = make_key('a', a, kw)
#    if key in cache:
#        return cache[key]
#    obj = f(*a, **kw)
#    cache[key] = obj
#    return obj
            
