from util import clear_tag

def invalidate_user(user):
    clear_tag(user)

def invalidate_delegateable(d):
    clear_tag(d)
    for p in d.parents:
        invalidate_delegateable(p)
        
def invalidate_revision(rev):
    invalidate_comment(rev.comment)
    
def invalidate_karma(karma):
    invalidate_comment(karma.comment)
    
def invalidate_comment(comment):
    clear_tag(comment)
    if comment.reply:
        invalidate_comment(comment.reply)
    invalidate_delegateable(comment.topic)
    
def invalidate_delegation(delegation):    
    invalidate_user(delegation.principal)
    invalidate_user(delegation.agent)
    
def invalidate_vote(vote):
    clear_tag(vote)
    invalidate_user(vote.user)
    invalidate_poll(vote.poll)
    
def invalidate_poll(poll):
    clear_tag(poll)
    invalidate_delegateable(poll.proposal)
    
def invalidate_instance(instance):
    # muharhar cache epic fail 
    clear_tag(instance)
    for d in instance.delegateables:
        invalidate_delegateable(d)