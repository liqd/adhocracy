import logging

from adhocracy import model

import instance_tiles as instance
import comment_tiles as comment
import user_tiles as user
import proposal_tiles as proposal
import event_tiles as event
import decision_tiles as decision
import delegation_tiles as delegation
import revision_tiles as revision
import page_tiles as page
import poll_tiles as poll
import tag_tiles as tag
import text_tiles as text
import selection_tiles as selection
import milestone_tiles as milestone


log = logging.getLogger(__name__)

def dispatch_row_with_comments(entity):
    if isinstance(entity, model.Comment):
        return comment.row(entity)
    return dispatch_row(entity)

def dispatch_row(entity):
    if isinstance(entity, model.User):
        return user.row(entity)
    elif isinstance(entity, model.Instance):
        return instance.row(entity)
    elif isinstance(entity, model.Proposal):
        return proposal.row(entity)
    elif isinstance(entity, model.Milestone):
        return milestone.row(entity)
    elif isinstance(entity, model.Page):
        if entity.function != model.Page.DESCRIPTION:
            return page.row(entity)
    elif isinstance(entity, model.Tag):
        return tag.row(entity)
    else:
        pass 
        #log.warn("WARNING: Cannot render %s!" % repr(entity))

