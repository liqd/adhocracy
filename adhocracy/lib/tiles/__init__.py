import logging

from adhocracy import model

import issue_tiles as issue
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


log = logging.getLogger(__name__)


def dispatch_row(entity):
    if isinstance(entity, model.User):
        return user.row(entity)
    elif isinstance(entity, model.Instance):
        return instance.row(entity)
    elif isinstance(entity, model.Issue):
        return issue.row(entity)
    elif isinstance(entity, model.Proposal):
        return proposal.row(entity)
    elif isinstance(entity, model.Page):
        return page.row(entity)
    elif isinstance(entity, model.Tag):
        return tag.row(entity)
    #elif isinstance(entity, model.Comment):
    #    return comment.row(entity)
    else: 
        log.warn("WARNING: Cannot render %s!" % repr(entity))

