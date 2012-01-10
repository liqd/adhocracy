import logging

import adhocracy.model as model

from util import memoize
from invalidate import (invalidate_user, invalidate_vote, invalidate_page,
                        invalidate_delegateable, invalidate_delegation,
                        invalidate_revision, invalidate_comment,
                        invalidate_poll, invalidate_tagging, invalidate_text,
                        invalidate_selection, invalidate_badge)

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
    model.Selection: invalidate_selection,
    model.badge: invalidate_badge
    }


def invalidate(entity):
    try:
        from pylons import g
        if g.cache is not None:
            func = HANDLERS.get(entity.__class__, lambda x: x)
            func(entity)
    except TypeError:
        pass
