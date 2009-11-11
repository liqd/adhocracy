import adhocracy.model as model

import decision
from decision import Decision

import delegation_node
from delegation_node import DelegationNode

#import poll
#from poll import Poll, PollException, NoPollException

import result
from result import Result

# TODO: Principals length

# TODO: Delegation replay


def is_motion_mutable(motion):
    """
    Find out whether a motion can be modified in its current polling 
    state. 
    """    
    result = Result(motion)
    return not result.polling

def is_comment_mutable(comment):
    """
    Find out whether a comment is a canonical contribution to a motion 
    that is currently polling.
    """
    if not comment.canonical:
        return True
    if isinstance(comment.topic, model.Motion):
        return is_motion_mutable(comment.topic)
    return True

def can_motion_cancel(motion):
    """
    Find out whether a motion can be modified in its current polling 
    state. 
    """
    result = Result(motion)
    return result.can_cancel