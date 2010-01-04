import logging
import re

from pylons.i18n import _ 

from vote import Vote
from user import User
from group import Group
from permission import Permission
from comment import Comment
from delegation import Delegation
from category import Category
from issue import Issue
from motion import Motion
from poll import Poll
from instance import Instance

log = logging.getLogger(__name__)

FORMAT = re.compile("@\[(.*):(.*)\]")

TYPES = [Vote,
         User,
         Group,
         Permission,
         Comment,
         Delegation,
         Category,
         Issue,
         Motion,
         Poll,
         Instance]

def entity_type(cls):
    return cls.__tablename__

def to_ref(entity):
    for cls in TYPES:
        if isinstance(entity, cls):
            return u"@[%s:%s]" % (entity_type(entity), str(entity._index_id()))
    return entity

def ref_type(ref):
    match = FORMAT.match(ref)
    if not match:
        return None
    return match.group(1)

def to_entity(ref, instance_filter=False):
    match = FORMAT.match(unicode(ref))
    if not match:
        return ref
    for cls in TYPES:
        if match.group(1) == entity_type(cls):
            entity = cls.find(match.group(2), 
                              instance_filter=instance_filter)
            #log.debug("entityref reloaded: %s" % repr(entity))
            return entity
    log.warn("No typeformatter for: %s" % ref)
    return ref
    
def _ify(fun, obj):
    if isinstance(obj, type([])):
        return [refify(e) for e in obj]
    elif isinstance(obj, type({})):
        return dict([(k, _ify(fun, v)) for k, v in obj.items()])
    else:
        if obj:
            obj = fun(obj)
            if not obj:
                obj = _("(Undefined)") 
        return obj
    
complex_to_refs = lambda obj: _ify(to_ref, obj)
complex_to_entities = lambda obj: _ify(to_entity, obj)

        
