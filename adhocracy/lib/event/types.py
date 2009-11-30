from pylons.i18n import _

class NotificationType(object):
    def __init__(self, code, pri, subject, notify_self=False):
        self.code = code
        self.priority = pri
        self.subject = subject
        self.notify_self = notify_self
        
    def __str__(self):
        return self.code
    
    def __repr__(self):
        return self.code
        
class EventType(NotificationType):
    def __init__(self, code, pri, subject, event_msg, notify_self=False):
        self.event_msg = event_msg
        super(EventType, self).__init__(code, pri, subject, notify_self=notify_self)
    

T_USER_CREATE = EventType(u"t_user_create", pri=2, 
                          subject=lambda: _(u"New user: %(agent)s"),
                          event_msg=lambda: _(u"signed up"))

T_USER_EDIT = EventType(u"t_account_edit", pri=1, 
                          subject=lambda: _(u"%(agent)s: profile updated"),
                          event_msg=lambda: _(u"edited their profile"),
                          notify_self=True)

T_USER_ADMIN_EDIT = EventType(u"t_account_admin_edit", pri=2, 
                          subject=lambda: _(u"%(user)s: profile was edited by %(agent)s"),
                          event_msg=lambda: _(u"edited %(user)ss profile"),
                          notify_self=True)

T_INSTANCE_CREATE = EventType(u"t_instance_create", pri=3, 
                          subject=lambda: _(u"New Adhocracy: %(instance)s"),
                          event_msg=lambda: _(u"founded the %(instance)s Adhocracy"))

T_INSTANCE_EDIT = EventType(u"t_instance_edit", pri=3, 
                          subject=lambda: _(u"%(instance)s: Adhocracy was updated"),
                          event_msg=lambda: _(u"updated the %(instance)s Adhocracy"))

T_INSTANCE_DELETE = EventType(u"t_instance_delete", pri=3, 
                          subject=lambda: _(u"Deleted Adhocracy: %(instance)s"),
                          event_msg=lambda: _(u"deleted the %(instance)s Adhocracy"))

T_INSTANCE_JOIN = EventType(u"t_instance_join", pri=2, 
                          subject=lambda: _(u"%(instance)s: %(agent)s joined"),
                          event_msg=lambda: _(u"joined %(instance)s"))

T_INSTANCE_LEAVE = EventType(u"t_instance_leave", pri=2, 
                          subject=lambda: _(u"%(instance)s: %(agent)s left"),
                          event_msg=lambda: _(u"left %(instance)s"))

T_INSTANCE_FORCE_LEAVE = EventType(u"t_instance_force_leave", pri=3, 
                          subject=lambda: _(u"%(instance)s: %(user)s was forced to leave"),
                          event_msg=lambda: _(u"was forced to leave %(instance)s by %(user)s"))

T_INSTANCE_MEMBERSHIP_UPDATE = EventType(u"t_instance_membership_update", pri=3, 
                          subject=lambda: _(u"%(instance)s: %(agent)s is now a %(group)s"),
                          event_msg=lambda: _(u"now is a %(group)s within %(instance)s"))

T_ISSUE_CREATE = EventType(u"t_issue_create", pri=3, 
                          subject=lambda: _(u"New issue: %(issue)s"),
                          event_msg=lambda: _(u"created %(issue)s"))

T_ISSUE_EDIT = EventType(u"t_issue_edit", pri=1, 
                          subject=lambda: _(u"Edited issue: %(issue)s"),
                          event_msg=lambda: _(u"edited %(issue)s"))

T_ISSUE_DELETE = EventType(u"t_issue_delete", pri=2, 
                          subject=lambda: _(u"Deleted issue: %(issue)s"),
                          event_msg=lambda: _(u"deleted %(issue)s"))

T_MOTION_CREATE = EventType(u"t_motion_create", pri=3, 
                          subject=lambda: _(u"New motion: %(motion)s"),
                          event_msg=lambda: _(u"created %(motion)s"))

T_MOTION_EDIT = EventType(u"t_motion_edit", pri=1, 
                          subject=lambda: _(u"Edit motion: %(motion)s"),
                          event_msg=lambda: _(u"edited %(motion)s"))

T_MOTION_STATE_REDRAFT = EventType(u"t_motion_state_draft", pri=3, 
                          subject=lambda: _(u"Poll cancelled: %(motion)s"),
                          event_msg=lambda: _(u"re-drafted %(motion)s"))

T_MOTION_STATE_VOTING = EventType(u"t_motion_state_voting", pri=4, 
                          subject=lambda: _(u"New Poll: %(motion)s"),
                          event_msg=lambda: _(u"called a vote on %(motion)s"))

T_MOTION_DELETE = EventType(u"t_motion_delete", pri=2, 
                          subject=lambda: _(u"Deleted motion: %(motion)s"),
                          event_msg=lambda: _(u"deleted %(motion)s"))

T_CATEGORY_CREATE = EventType(u"t_category_create", pri=3, 
                          subject=lambda: _(u"New category: %(category)s"),
                          event_msg=lambda: _(u"created the category %(category)s in %(parent)s"))

T_CATEGORY_EDIT = EventType(u"t_category_edit", pri=2, 
                          subject=lambda: _(u"Edited category: %(category)s"),
                          event_msg=lambda: _(u"updated the category %(category)s"))

T_CATEGORY_DELETE = EventType(u"t_category_delete", pri=3, 
                          subject=lambda: _(u"Deleted category: %(category)s"),
                          event_msg=lambda: _(u"deleted the category %(category)s"))

T_COMMENT_CREATE = EventType(u"t_comment_create", pri=2, 
                          subject=lambda: _(u"New comment: in %(topic)s"),
                          event_msg=lambda: _(u"created a %(comment)s on %(topic)s"))

T_COMMENT_EDIT = EventType(u"t_comment_edit", pri=1, 
                          subject=lambda: _(u"Edited comment: in %(topic)s"),
                          event_msg=lambda: _(u"edited a %(comment)s on %(topic)s"))

T_COMMENT_DELETE = EventType(u"t_comment_delete", pri=2, 
                          subject=lambda: _(u"Deleted comment: in %(topic)s"),
                          event_msg=lambda: _(u"deleted a %(comment)s from %(topic)s"))

T_DELEGATION_CREATE = EventType(u"t_delegation_create", pri=2, 
                          subject=lambda: _(u"New Delegation: %(agent)s delegated %(scope)s to %(delegate)s"),
                          event_msg=lambda: _(u"delegated voting on %(scope)s to %(delegate)s"))

T_DELEGATION_REVOKE = EventType(u"t_delegation_revoke", pri=2, 
                          subject=lambda: _(u"Revoked Delegation: %(agent)s revoked delegation to %(delegate)s"),
                          event_msg=lambda: _(u"revoked their delegation on %(scope)s to %(delegate)s"))

T_VOTE_CAST = EventType(u"t_vote_cast", pri=2, 
                          subject=lambda: _(u"Vote: %(agent)s %(vote)s %(poll)s"),
                          event_msg=lambda: _(u"voted %(vote)s %(poll)s"))

T_TEST = EventType(u"t_test", pri=5, 
                          subject=lambda: _(u"Adhocracy says hello: %(test)s"),
                          event_msg=lambda: _(u"test %(test)s"))



N_DELEGATION_RECEIVED = NotificationType("n_delegation_receive", pri=4, 
                          subject=lambda: _(u"You received %(agent)ss delegation on %(scope)s"))

N_DELEGATION_LOST = NotificationType("n_delegation_lost", pri=4, 
                          subject=lambda: _(u"You lost %(agent)ss delegation on %(scope)s"))

N_INSTANCE_FORCE_LEAVE = NotificationType("n_instance_force_leave", pri=5, 
                          subject=lambda: _(u"Membership: You've been kicked from %(instance)s"),
                          notify_self=True)

N_INSTANCE_MEMBERSHIP_UPDATE = NotificationType("n_instance_membership_update", pri=4, 
                          subject=lambda: _(u"Membership: you're now a %(group)s in %(instance)s"),
                          notify_self=True)

N_SELF_VOTED = NotificationType("n_self_voted", pri=3, 
                          subject=lambda: _(u"Vote Confirmation: you %(vote)s %(poll)s"),
                          notify_self=True)

N_DELEGATE_VOTED = NotificationType("n_delegate_voted", pri=4, 
                          subject=lambda: _(u"Delegate Vote: you %(vote)s %(poll)s"),
                          notify_self=True)

N_DELEGATE_CONFLICT = NotificationType("n_delegate_conflict", pri=5, 
                          subject=lambda: _(u"Delegate Conflict: %(poll)s"),
                          notify_self=True)

N_COMMENT_REPLY = NotificationType("n_comment_reply", pri=4, 
                          subject=lambda: _(u"Comment Reply: %(topic)s"))

N_COMMENT_EDIT = NotificationType("n_comment_edit", pri=4, 
                          subject=lambda: _(u"Comment Edit: %(topic)s"))


# The funny thing about this line is: YOU DO NOT SEE IT!
TYPES = filter(lambda n: isinstance(n, NotificationType), map(eval, dir())) 
