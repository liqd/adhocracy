import logging

import adhocracy.model as model

from decision import Decision
from delegation_node import DelegationNode
from state import State

from ..cache import memoize
from .. import queue

log = logging.getLogger(__name__)

def init_democracy():
    try:
        for vote in model.Vote.all():
            if model.Tally.find_by_vote(vote) is None:
                handle_vote(vote)
    except Exception, e:
        log.warn("Cannot update tallies: %s" % e)
    
    queue.register(model.Vote, queue.INSERT, handle_vote)
    queue.register(model.Vote, queue.UPDATE, handle_vote)

def handle_vote(vote):
    log.debug("Post-processing vote: %s" % vote)
    if model.Tally.find_by_vote(vote) is None:
        tally = model.Tally.create_from_vote(vote)
        model.meta.Session.commit()
        log.debug("Tallied %s: %s" % (vote.poll, tally))
    
    

# RFACT: try to move all functionality out of here
def is_comment_mutable(comment):
    """
    Find out whether a comment is a canonical contribution to a proposal 
    that is currently polling.
    """
    if not comment.canonical:
        return True
    if isinstance(comment.topic, model.Proposal):
        return State(comment.topic).proposal_mutable
    return True

def is_proposal_mutable(proposal):
    return State(proposal).proposal_mutable

@memoize('number_of_votes')
def number_of_votes(user, topic):
    return user.number_of_votes_in_scope(topic)
