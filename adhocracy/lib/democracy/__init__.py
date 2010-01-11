import adhocracy.model as model

from decision import Decision
from delegation_node import DelegationNode
from state import State

from ..cache import memoize

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
