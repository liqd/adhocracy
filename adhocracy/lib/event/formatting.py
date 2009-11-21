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

class MotionFormatter(DelegateableFormatter):
    pass

class CategoryFormatter(DelegateableFormatter):
    pass
            
class InstanceFormatter(ObjectFormatter):
    
    def unicode(self, instance):
        return instance.label
    
    def html(self, instance):
        return u"<a class='event_instance' href='%s'>%s</a>" % (
                h.instance_url(instance),
                instance.label)
        
class UserFormatter(ObjectFormatter):
    
    def unicode(self, user):
        return user.name
    
    def html(self, user):
        return h.user_link(user, include_score=False)
    
class GroupFormatter(ObjectFormatter):
    
    def unicode(self, group):
        return group.group_name
    
    def html(self, group):
        return self.unicode(group)
    
class VoteFormatter(ObjectFormatter):
    
    def unicode(self, vote):
        return {1: _("voted for"),
                0: _("abstained on"),
               -1: _("voted against")}[vote.orientation]
    
    def html(self, value):
        return self.unicode(value)
    
class CommentFormatter(ObjectFormatter):
    
    def unicode(self, comment):
        return _("comment")
    
    def html(self, comment):
        return "<a href='/comment/r/%d'>%s</a>" % (comment.id, 
                                                 self.unicode(comment))

           
FORMATTERS = {model.Vote: VoteFormatter(),
              model.Group: GroupFormatter(),
              model.User: UserFormatter(),
              model.Instance: InstanceFormatter(),
              model.Category: CategoryFormatter(),
              model.Motion: MotionFormatter(),
              model.Issue: IssueFormatter(),
              model.Comment: CommentFormatter()}
