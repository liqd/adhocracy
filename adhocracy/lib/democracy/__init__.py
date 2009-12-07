import adhocracy.model as model

from decision import Decision
from delegation_node import DelegationNode
from state import State

# RFACT: try to move all functionality out of here
def is_comment_mutable(comment):
    """
    Find out whether a comment is a canonical contribution to a motion 
    that is currently polling.
    """
    if not comment.canonical:
        return True
    if isinstance(comment.topic, model.Motion):
        return State(comment.topic).motion_mutable
    return True
