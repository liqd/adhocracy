import logging

import adhocracy.model.hooks as hooks
import adhocracy.model as model

from util import memoize
from invalidate import *

log = logging.getLogger(__name__)

HANDLERS = {
    model.User: invalidate_user,
    model.Vote: invalidate_vote,
    model.Page: invalidate_page,
    model.Proposal: invalidate_delegateable,
    model.Delegation: invalidate_delegation,
    model.Revision: invalidate_revision,
    model.Comment: invalidate_comment,
    model.Poll: invalidate_poll,
    model.Tagging: invalidate_tagging,
    model.Text: invalidate_text,
    model.Selection: invalidate_selection
    }

def invalidate(entity):
    try:
        from pylons import g
        if g.cache is not None:
            func = HANDLERS.get(entity.__class__, lambda x: x)
            func(entity)
    except TypeError, te:
        pass
