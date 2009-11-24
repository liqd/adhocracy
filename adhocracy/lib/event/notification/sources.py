
from ... import watchlist
from notification import Notification
from ..types import *
import adhocracy.model as model

class WatchlistSource(object):
    """
    Traverse the watchlist for all affected topics. Returns only the most closely matching 
    watchlist entries.
    """
    
    def __init__(self):
        pass
    
    def _merge(self, large_scope, small_scope):
        for small in small_scope:
            keep_list = []
            for large in large_scope:
                if not large.user == small.user:
                    keep_list.append(large)
            large_scope = keep_list
        return small_scope + large_scope
    
    def _delegateable(self, delegateable):
        watches = []
        for parent in delegateable.parents:
            watches += self._delegateable(parent)
        return self._merge(watches, 
                      watchlist.get_entity_watches(delegateable))
    
    def _comment(self, comment):
        watches = [] 
        if comment.reply:
            watches += self._comment(comment.reply)
        else:
            watches += self._delegateable(comment.topic)
        return self._merge(watches, 
                      watchlist.get_entity_watches(comment))
    
    def _watches(self, event):
        watches = watchlist.get_entity_watches(event.agent)
        for topic in event.topics:
            if isinstance(topic, model.Comment):
                watches = self._merge(self._comment(topic), watches)
            elif isinstance(topic, model.Delegateable):
                watches = self._merge(self._delegateable(topic), watches) 
            else:
                watches = self._merge(watchlist.get_entity_watches(topic), watches)
        return watches
                
    def __call__(self, event):
        for watch in self._watches(event): 
            yield Notification(event, watch.user, watch=watch)

watchlist_source = WatchlistSource() # yeah no its not a 'real' class.

from ... import democracy       
def vote_source(event):
    """
    Notify users about their voting behaviour, especially about delegated votes.
    """
    if event.event == T_VOTE_CAST:
        decision = democracy.Decision(evetn.agent, event.poll)
        if not decision.made():
            yield Notification(event, event.agent, type=N_DELEGATE_CONFLICT)
        elif decision.self_made():
            yield Notification(event, event.agent, type=N_SELF_VOTED)
        else:
            yield Notification(event, event.agent, type=N_DELEGATE_VOTED)

def delegation_source(event):
    """
    Notifiy users of gained and lost delegations.
    """
    if event.event == T_DELEGATION_CREATE:
        yield Notification(event, event.delegate, type=N_DELEGATION_RECEIVED)
    elif event.event == T_DELEGATION_REVOKE:
        yield Notification(event, event.delegate, type=N_DELEGATION_LOST)

def instance_source(event):
    """
    Notifiy users of changes in their instance membership.
    """
    if event.event == T_INSTANCE_FORCE_LEAVE:
        yield Notification(event, event.agent, type=N_INSTANCE_FORCE_LEAVE)
    elif event.event == T_INSTANCE_MEMBERSHIP_UPDATE:
        yield Notification(event, event.agent, type=N_INSTANCE_MEMBERSHIP_UPDATE)

def comment_source(event):
    """
    Transform comment edits and replies into personal messages.
    """    
    # for all authors who want to be notified of edits: 
    if event.event == T_COMMENT_EDIT:
        for rev in event.comment.revisions:
            watch = watchlist.get_entity_watch(rev.user, event.comment)
            if watch: 
                yield Notification(event, rev.user, type=N_COMMENT_EDIT, watch=watch)
                
    # for all authors who want to be notified of replies:
    elif event.event == T_COMMENT_CREATE:
        def _rec(comment):
            for rev in event.comment.revisions:
                watch = watchlist.get_entity_watch(rev.user, event.comment)
                if watch:
                    yield Notification(event, rev.user, type=N_COMMENT_REPLY, watch=watch)
            if comment.reply:
                for n in _rec(comment.reply): yield n
        for n in _rec(event.comment): yield n