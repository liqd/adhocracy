
from ...text import i18n

class Notification(object):
    
    def __init__(self, event, user, type=None, watch=None):
        self.event = event
        self._type = type
        self.user = user
        self.watch = watch
        
    def get_type(self):
        if not self._type:
            return self.event.event
        return self._type
        
    type = property(get_type)

    def get_priority(self):
        return self.type.pri
        
    priority = property(get_priority)
    
    def get_id(self):
        return "n-e%s-u%s" % (self.event.id, self.user.id)
    
    id = property(get_id)
    
    def language_context(self):
        return i18n.user_language(self.user)
    
    def get_subject(self):
        return self.event.event
    
    subject = property(get_subject)
    
    def get_body(self):
        return self.event.agent.name + " " + unicode(self.event)
    
    body = property(get_body)
            
    def __repr__(self):
        return "<Notification(%s,%s)>" % (self.event, self.user.user_name)
    