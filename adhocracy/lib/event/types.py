from pylons.i18n import _

class NotificationType(object):
    def __init__(self, code, pri, subject, body_tpl):
        self.code = code
        self.priority = pri
        self.subject = subject
        self.body_tpl = body_tpl
        
    def __str__(self):
        return self.code
    
    def __repr__(self):
        return self.code
        
class EventType(NotificationType):
    def __init__(self, code, pri, subject, event_msg, body_tpl):
        self.event_msg = event_msg
        super(EventType, self).__init__(code, pri, subject, body_tpl)
    

T_USER_CREATE = EventType(u"t_user_create", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"signed up"),
                          body_tpl='')

T_USER_EDIT = EventType(u"t_account_edit", pri=1, 
                          subject=None,
                          event_msg=lambda: _(u"edited their profile"),
                          body_tpl='')

T_USER_ADMIN_EDIT = EventType(u"t_account_admin_edit", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"edited %(user)ss profile"),
                          body_tpl='')

T_INSTANCE_CREATE = EventType(u"t_instance_create", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"founded the %(instance)s Adhocracy"),
                          body_tpl='')

T_INSTANCE_EDIT = EventType(u"t_instance_edit", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"updated the %(instance)s Adhocracy"),
                          body_tpl='')

T_INSTANCE_DELETE = EventType(u"t_instance_delete", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"deleted the %(instance)s Adhocracy"),
                          body_tpl='')

T_INSTANCE_JOIN = EventType(u"t_instance_join", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"joined %(instance)s"),
                          body_tpl='')

T_INSTANCE_LEAVE = EventType(u"t_instance_leave", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"left %(instance)s"),
                          body_tpl='')

T_INSTANCE_FORCE_LEAVE = EventType(u"t_instance_force_leave", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"was forced to leave %(instance)s by %(user)s"),
                          body_tpl='')

T_INSTANCE_MEMBERSHIP_UPDATE = EventType(u"t_instance_membership_update", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"now is a %(group)s within %(instance)s"),
                          body_tpl='')

T_ISSUE_CREATE = EventType(u"t_issue_create", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"created %(issue)s"),
                          body_tpl='')

T_ISSUE_EDIT = EventType(u"t_issue_edit", pri=1, 
                          subject=None,
                          event_msg=lambda: _(u"edited %(issue)s"),
                          body_tpl='')

T_ISSUE_DELETE = EventType(u"t_issue_delete", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"deleted %(issue)s"),
                          body_tpl='')

T_MOTION_CREATE = EventType(u"t_motion_create", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"created %(motion)s"),
                          body_tpl='')

T_MOTION_EDIT = EventType(u"t_motion_edit", pri=1, 
                          subject=None,
                          event_msg=lambda: _(u"edited %(motion)s"),
                          body_tpl='')

T_MOTION_STATE_REDRAFT = EventType(u"t_motion_state_draft", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"re-drafted %(motion)s"),
                          body_tpl='')

T_MOTION_STATE_VOTING = EventType(u"t_motion_state_voting", pri=4, 
                          subject=None,
                          event_msg=lambda: _(u"called a vote on %(motion)s"),
                          body_tpl='')

T_MOTION_DELETE = EventType(u"t_motion_delete", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"deleted %(motion)s"),
                          body_tpl='')

T_CATEGORY_CREATE = EventType(u"t_category_create", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"created the category %(category)s in %(parent)s"),
                          body_tpl='')

T_CATEGORY_EDIT = EventType(u"t_category_edit", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"updated the category %(category)s"),
                          body_tpl='')

T_CATEGORY_DELETE = EventType(u"t_category_delete", pri=3, 
                          subject=None,
                          event_msg=lambda: _(u"deleted the category %(category)s"),
                          body_tpl='')

T_COMMENT_CREATE = EventType(u"t_comment_create", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"created a %(comment)s on %(topic)s"),
                          body_tpl='')

T_COMMENT_EDIT = EventType(u"t_comment_edit", pri=1, 
                          subject=None,
                          event_msg=lambda: _(u"edited a %(comment)s on %(topic)s"),
                          body_tpl='')

T_COMMENT_DELETE = EventType(u"t_comment_delete", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"deleted a %(comment)s from %(topic)s"),
                          body_tpl='')

T_DELEGATION_CREATE = EventType(u"t_delegation_create", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"delegated voting on %(scope)s to %(delegate)s"),
                          body_tpl='')

T_DELEGATION_REVOKE = EventType(u"t_delegation_revoke", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"revoked their delegation on %(scope)s to %(delegate)s"),
                          body_tpl='')

T_VOTE_CAST = EventType(u"t_vote_cast", pri=2, 
                          subject=None,
                          event_msg=lambda: _(u"%(vote)s %(poll)s"),
                          body_tpl='')

T_TEST = EventType(u"t_test", pri=5, 
                          subject=None,
                          event_msg=lambda: _(u"test %(test)s"),
                          body_tpl='')

N_DELEGATION_RECEIVED = NotificationType("n_delegation_receive", pri=4, 
                          subject=None,
                          body_tpl='')

N_DELEGATION_LOST = NotificationType("n_delegation_lost", pri=4, 
                          subject=None,
                          body_tpl='')

N_INSTANCE_FORCE_LEAVE = NotificationType("n_instance_force_leave", pri=5, 
                          subject=None,
                          body_tpl='')

N_INSTANCE_MEMBERSHIP_UPDATE = NotificationType("n_instance_membership_update", pri=4, 
                          subject=None,
                          body_tpl='')

N_SELF_VOTED = NotificationType("n_self_voted", pri=3, 
                          subject=None,
                          body_tpl='')

N_DELEGATE_VOTED = NotificationType("n_delegate_voted", pri=4, 
                          subject=None,
                          body_tpl='')

N_DELEGATE_CONFLICT = NotificationType("n_delegate_conflict", pri=5, 
                          subject=None,
                          body_tpl='')

N_COMMENT_REPLY = NotificationType("n_comment_reply", pri=4, 
                          subject=None,
                          body_tpl='')

N_COMMENT_EDIT = NotificationType("n_comment_edit", pri=4, 
                          subject=None,
                          body_tpl='')

TYPES = filter(lambda n: isinstance(n, NotificationType), dir())