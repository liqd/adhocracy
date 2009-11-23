
from ...text import i18n
from types import PRIORITIES

class Notification(object):
    
    def __init__(self, event, user, type=None, watch=None, priority=None):
        self.event = event
        self._type = type
        self.user = user
        self.watch = watch
        self._priority = priority
        
    def get_type(self):
        if not self._type:
            return self.event.event
        return self._type
        
    type = property(get_type)

    def get_priority(self):
        if not self._priority:
            return PRIORITIES[self.type]
        
    priority = property(get_priority)
    
    def get_id(self):
        return "n-e%s-u%s" % (self.event.id, self.user.id)
    
    id = property(get_id)
    
    def language_context(self):
        return i18n.user_language(self.user)
    
    def get_subject(self):
        return self.event.event
    
    subject = property(get_subject)
    
    def get_plain_body(self):
        return self.event.agent.name + " " + unicode(self.event)
    
    plain_body = property(get_plain_body)
    
    def get_html_body(self):
        return self.event.to_json()
    
    html_body = property(get_html_body)
        
    def __repr__(self):
        return "<Notification(%s,%s)>" % (self.event, self.user.user_name)
    