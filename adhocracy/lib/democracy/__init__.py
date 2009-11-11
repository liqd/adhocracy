import adhocracy.model as model

import decision
from decision import Decision

import delegation_node
from delegation_node import DelegationNode

import state
from state import State

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
