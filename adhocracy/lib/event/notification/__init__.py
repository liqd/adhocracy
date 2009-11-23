from .... import watchlist
 
class Notification(object):
    
    def __init__(self, event, user, priority=None):
        self.event = event
        self.user = user
        self.priority = priority

def watchlist_notifications(event):
    
    def _delegateable(delegateable):
        watches = watchlist.get_entity_watches(delegateable)
        for parent in delegateable.parents:
            watches += _delegateable(parent)
        return watches
    
    def _comment(comment):
        watches = watchlist.get_entity_watches(comment)
        if comment.reply:
            watches += _comment(comment.reply)
        else:
            watches += _delegateable(comment.topic)
        return watches
    
    watches = watchlist.get_entity_watches(event.agent)
    for topic in event.topics:
        if isinstance(topic, model.Comment):
            watches += _comment(topic)
        elif isinstance(topic, model.Delegateable):
            watches += _delegateable(topic) 
        elif isinstance(topic, model.User):
            watches += watchlist.get_entity_watches(topic)
    return watches