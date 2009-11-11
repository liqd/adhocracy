import logging
import re

from adhocracy import model

log = logging.getLogger(__name__)

FORMAT = re.compile("@\[(.*):(.*)\]")

TYPES = [model.Vote,
         model.User,
         model.Group,
         model.Permission,
         model.Comment,
         model.Delegation,
         model.Category,
         model.Issue,
         model.Motion,
         model.Instance]

def _index_name(cls):
    return cls.__tablename__

def to_ref(entity):
    for cls in TYPES:
        if isinstance(entity, cls):
            return "@[%s:%s]" % (_index_name(entity), str(entity._index_id()))
    return entity

def to_entity(ref):
    match = FORMAT.match(ref)
    if not match:
        return ref
    for cls in TYPES:
        if match.group(1) == _index_name(cls):
            entity = cls.find(match.group(2), 
                              instance_filter=False)
            #log.debug("entityref reloaded: %s" % repr(entity))
            return entity
    log.warn("No typeformatter for: %s" % ref)
    return ref

