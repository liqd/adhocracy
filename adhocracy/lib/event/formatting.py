from pylons.i18n import _ 

import adhocracy.model as model
from .. import helpers as h

DT_FORMAT = "%Y%m%d%H%M%S"

class ObjectFormatter(object):
    
    def unicode(self, value):
        return value
    
    def html(self, value):
        return value

class DelegateableFormatter(ObjectFormatter):
    
    def unicode(self, delegateable):
        return delegateable.label
    
    def html(self, delegateable):
        return h.delegateable_link(delegateable)

class IssueFormatter(DelegateableFormatter):
    pass

class ProposalFormatter(DelegateableFormatter):
    pass

class PollFormatter(ObjectFormatter):
    # TODO fixme
    
    def unicode(self, poll):
        m = DelegateableFormatter()
        return m.unicode(poll.scope)
    
    def html(self, poll):
        m = DelegateableFormatter()
        return m.html(poll.scope)
            
class InstanceFormatter(ObjectFormatter):
    
    def unicode(self, instance):
        return instance.label
    
    def html(self, instance):
        return u"<a class='event_instance' href='%s'>%s</a>" % (
                h.entity_url(instance),
                instance.label)
        
class UserFormatter(ObjectFormatter):
    
    def unicode(self, user):
        return user.name
    
    def html(self, user):
        return h.user_link(user)
    
class GroupFormatter(ObjectFormatter):
    
    def unicode(self, group):
        return _(group.group_name)
    
    def html(self, group):
        return self.unicode(group)
    
class VoteFormatter(ObjectFormatter):
    
    def unicode(self, vote):
        return {1: _("for"),
                0: _("to abstain"),
               -1: _("against")}[vote.orientation]
    
    def html(self, value):
        return self.unicode(value)
    
class CommentFormatter(ObjectFormatter):
    
    def unicode(self, comment):
        return _("comment")
    
    def html(self, comment):
        if comment.delete_time:
            return self.unicode(comment)
        return "<a href='%s'>%s</a>" % (h.entity_url(comment), 
                                       self.unicode(comment))


class FormattedEvent(object): 
               
    FORMATTERS = {model.Vote: VoteFormatter(),
              model.Group: GroupFormatter(),
              model.User: UserFormatter(),
              model.Instance: InstanceFormatter(),
              model.Proposal: ProposalFormatter(),
              model.Poll: PollFormatter(),
              model.Issue: IssueFormatter(),
              model.Comment: CommentFormatter()}
    
    def __init__(self, event, decoder):
        self.event = event
        self.decoder = decoder
        
    def __getitem__(self, item):
        try:
            value = self.event[item]
            for cls in self.FORMATTERS.keys():
                if isinstance(value, cls):
                    return self.decoder(self.FORMATTERS[cls], value)
            return value
        except AttributeError:
            return _("(Undefined)")
    
def as_unicode(event):
    fe = FormattedEvent(event, lambda f, value: f.unicode(value))
    return event.event.event_msg() % fe

def as_html(event):
    fe = FormattedEvent(event, lambda f, value: f.html(value))
    return event.event.event_msg() % fe
    
