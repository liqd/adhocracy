from datetime import datetime
import logging

from lucene import Term

import adhocracy.model as model

log = logging.getLogger(__name__)


class EventException(Exception):
    pass

class EventFormattingException(EventException):
    pass

def hash_term(hash):
    """
    Creates a lucene query term that uniquely searches for this item.
    """
    return Term("_event_hash", str(hash))

def objtoken(obj):
    """
    Encode some known object types for use in event topic, scope, etc.
    Maybe this could be replaced by generic hashing? The current method 
    has the advantage of allowing admins to hand-write queries at some 
    point. 
    """
    if isinstance(obj, model.User):
        return "user.%s" % obj.user_name.lower()
    elif isinstance(obj, model.Category):
        return "category.%s" % obj.id.lower()
    elif isinstance(obj, model.Motion):
        return "motion.%s" % obj.id.lower()
    elif isinstance(obj, model.Issue):
        return "issue.%s" % obj.id.lower()
    elif isinstance(obj, model.Delegation):
        return "delegation.%s" % obj.id
    elif isinstance(obj, model.Instance):
        return "instance.%s" % obj.key.lower()
    return str(abs(hash(obj)))