from pylons.i18n import _
from .. import helpers as h

class NotificationType(object):
    def __init__(self, code, pri, subject, link_path, notify_self=False):
        self.code = code
        self.priority = pri
        self.subject = subject
        self.link_path = link_path
        self.notify_self = notify_self
        
    def __str__(self):
        return self.code
    
    def __repr__(self):
        return self.code
        
class EventType(NotificationType):
    def __init__(self, code, pri, subject, link_path, event_msg, notify_self=False):
        self.event_msg = event_msg
        super(EventType, self).__init__(code, pri, subject, link_path, notify_self=notify_self)
    

T_USER_CREATE = EventType(u"t_user_create", pri=2, 
                          subject=lambda: _(u"New user: %(user)s"),
                          link_path=lambda e: h.entity_url(e.user), 
                          event_msg=lambda: _(u"signed up"))

T_USER_EDIT = EventType(u"t_user_edit", pri=1, 
                          subject=lambda: _(u"%(user)s: profile updated"),
                          link_path=lambda e: h.entity_url(e.user), 
                          event_msg=lambda: _(u"edited their profile"),
                          notify_self=True)

T_USER_ADMIN_EDIT = EventType(u"t_user_admin_edit", pri=2, 
                          subject=lambda: _(u"%(user)s: profile was edited by %(admin)s"),
                          link_path=lambda e: h.entity_url(e.user), 
                          event_msg=lambda: _(u"had their profile updated by %(admin)s"),
                          notify_self=True)

T_INSTANCE_CREATE = EventType(u"t_instance_create", pri=3, 
                          subject=lambda: _(u"New Adhocracy: %(instance)s"),
                          link_path=lambda e: h.entity_url(e.user), 
                          event_msg=lambda: _(u"founded the %(instance)s Adhocracy"))

T_INSTANCE_EDIT = EventType(u"t_instance_edit", pri=3, 
                          subject=lambda: _(u"%(instance)s: Adhocracy was updated"),
                          link_path=lambda e: h.entity_url(e.instance), 
                          event_msg=lambda: _(u"updated the %(instance)s Adhocracy"))

T_INSTANCE_DELETE = EventType(u"t_instance_delete", pri=3, 
                          subject=lambda: _(u"Deleted Adhocracy: %(instance)s"),
                          link_path=lambda e: h.entity_url(e.instance), 
                          event_msg=lambda: _(u"deleted the %(instance)s Adhocracy"))

T_INSTANCE_JOIN = EventType(u"t_instance_join", pri=2, 
                          subject=lambda: _(u"%(instance)s: %(user)s joined"),
                          link_path=lambda e: h.entity_url(e.user),
                          event_msg=lambda: _(u"joined %(instance)s"))

T_INSTANCE_LEAVE = EventType(u"t_instance_leave", pri=2, 
                          subject=lambda: _(u"%(instance)s: %(user)s left"),
                          link_path=lambda e: h.entity_url(e.user),
                          event_msg=lambda: _(u"left %(instance)s"))

T_INSTANCE_FORCE_LEAVE = EventType(u"t_instance_force_leave", pri=3, 
                          subject=lambda: _(u"%(instance)s: %(user)s was forced to leave"),
                          link_path=lambda e: h.entity_url(e.user),
                          event_msg=lambda: _(u"was forced to leave %(instance)s by %(admin)s"))

T_INSTANCE_MEMBERSHIP_UPDATE = EventType(u"t_instance_membership_update", pri=3, 
                          subject=lambda: _(u"%(instance)s: %(user)s is now a %(group)s"),
                          link_path=lambda e: h.entity_url(e.user),
                          event_msg=lambda: _(u"now is a %(group)s within %(instance)s"))

T_ISSUE_CREATE = EventType(u"t_issue_create", pri=4, 
                          subject=lambda: _(u"New issue: %(issue)s"),
                          link_path=lambda e: h.entity_url(e.issue),
                          event_msg=lambda: _(u"created %(issue)s"))

T_ISSUE_EDIT = EventType(u"t_issue_edit", pri=1, 
                          subject=lambda: _(u"Edited issue: %(issue)s"),
                          link_path=lambda e: h.entity_url(e.issue),
                          event_msg=lambda: _(u"edited %(issue)s"))

T_ISSUE_DELETE = EventType(u"t_issue_delete", pri=2, 
                          subject=lambda: _(u"Deleted issue: %(issue)s"),
                          link_path=lambda e: h.entity_url(e.issue),
                          event_msg=lambda: _(u"deleted %(issue)s"))

T_PROPOSAL_CREATE = EventType(u"t_proposal_create", pri=4, 
                          subject=lambda: _(u"New proposal: %(proposal)s"),
                          link_path=lambda e: h.entity_url(e.proposal),
                          event_msg=lambda: _(u"created %(proposal)s"))

T_PROPOSAL_EDIT = EventType(u"t_proposal_edit", pri=1, 
                          subject=lambda: _(u"Edit proposal: %(proposal)s"),
                          link_path=lambda e: h.entity_url(e.proposal),
                          event_msg=lambda: _(u"edited %(proposal)s"))

T_PROPOSAL_STATE_REDRAFT = EventType(u"t_proposal_state_draft", pri=3, 
                          subject=lambda: _(u"Poll cancelled: %(proposal)s"),
                          link_path=lambda e: h.entity_url(e.proposal),
                          event_msg=lambda: _(u"re-drafted %(proposal)s"))

T_PROPOSAL_STATE_VOTING = EventType(u"t_proposal_state_voting", pri=4, 
                          subject=lambda: _(u"New Poll: %(proposal)s"),
                          link_path=lambda e: h.entity_url(e.proposal),
                          event_msg=lambda: _(u"called a vote on %(proposal)s"))

T_PROPOSAL_DELETE = EventType(u"t_proposal_delete", pri=2, 
                          subject=lambda: _(u"Deleted proposal: %(proposal)s"),
                          link_path=lambda e: h.entity_url(e.proposal),
                          event_msg=lambda: _(u"deleted %(proposal)s"))

T_COMMENT_CREATE = EventType(u"t_comment_create", pri=2, 
                          subject=lambda: _(u"New comment: in %(topic)s"),
                          link_path=lambda e: h.entity_url(e.comment),
                          event_msg=lambda: _(u"created a %(comment)s on %(topic)s"))

T_COMMENT_EDIT = EventType(u"t_comment_edit", pri=1, 
                          subject=lambda: _(u"Edited comment: in %(topic)s"),
                          link_path=lambda e: h.entity_url(e.comment),
                          event_msg=lambda: _(u"edited a %(comment)s on %(topic)s"))

T_COMMENT_DELETE = EventType(u"t_comment_delete", pri=2, 
                          subject=lambda: _(u"Deleted comment: in %(topic)s"),
                          link_path=lambda e: h.entity_url(e.topic),
                          event_msg=lambda: _(u"deleted a %(comment)s from %(topic)s"))

T_DELEGATION_CREATE = EventType(u"t_delegation_create", pri=2, 
                          subject=lambda: _(u"New Delegation: %(user)s delegated %(scope)s to %(agent)s"),
                          link_path=lambda e: h.entity_url(e.scope),
                          event_msg=lambda: _(u"delegated voting on %(scope)s to %(agent)s"))

T_DELEGATION_REVOKE = EventType(u"t_delegation_revoke", pri=2, 
                          subject=lambda: _(u"Revoked Delegation: %(user)s revoked delegation to %(agent)s"),
                          link_path=lambda e: h.entity_url(e.scope),
                          event_msg=lambda: _(u"revoked their delegation on %(scope)s to %(agent)s"))

T_VOTE_CAST = EventType(u"t_vote_cast", pri=2, 
                          subject=lambda: _(u"Vote: %(user)s %(vote)s %(poll)s"),
                          link_path=lambda e: h.entity_url(e.poll.subject),
                          event_msg=lambda: _(u"voted %(vote)s %(poll)s"))

T_TEST = EventType(u"t_test", pri=5, 
                          subject=lambda: _(u"Adhocracy says hello: %(test)s"),
                          link_path=lambda e: "/",
                          event_msg=lambda: _(u"test %(test)s"))



N_DELEGATION_RECEIVED = NotificationType("n_delegation_receive", pri=4, 
                          subject=lambda: _(u"You received %(user)ss delegation on %(scope)s"),
                          link_path=lambda e: h.entity_url(e.scope))

N_DELEGATION_LOST = NotificationType("n_delegation_lost", pri=4, 
                          subject=lambda: _(u"You lost %(user)ss delegation on %(scope)s"),
                          link_path=lambda e: h.entity_url(e.scope))

N_INSTANCE_FORCE_LEAVE = NotificationType("n_instance_force_leave", pri=5, 
                          subject=lambda: _(u"Membership: You've been kicked from %(instance)s"),
                          link_path=lambda e: h.entity_url(e.instance),
                          notify_self=True)

N_INSTANCE_MEMBERSHIP_UPDATE = NotificationType("n_instance_membership_update", pri=4, 
                          subject=lambda: _(u"Membership: you're now a %(group)s in %(instance)s"),
                          link_path=lambda e: h.entity_url(e.instance),
                          notify_self=True)

N_SELF_VOTED = NotificationType("n_self_voted", pri=3, 
                          subject=lambda: _(u"You have voted %(vote)s %(poll)s"),
                          link_path=lambda e: h.entity_url(e.poll.subject),
                          notify_self=True)

N_DELEGATE_VOTED = NotificationType("n_delegate_voted", pri=4, 
                          subject=lambda: _(u"Your delegate %(agent)s has voted %(vote)s %(poll)s"),
                          link_path=lambda e: h.entity_url(e.poll.subject),
                          notify_self=True)

N_DELEGATE_CONFLICT = NotificationType("n_delegate_conflict", pri=5, 
                          subject=lambda: _(u"Delegate conflict regarding %(poll)s"),
                          link_path=lambda e: h.entity_url(e.poll.subject),
                          notify_self=True)

N_COMMENT_REPLY = NotificationType("n_comment_reply", pri=4, 
                          subject=lambda: _(u"Comment Reply: %(topic)s"),
                          link_path=lambda e: h.entity_url(e.comment))

N_COMMENT_EDIT = NotificationType("n_comment_edit", pri=4, 
                          subject=lambda: _(u"Comment Edit: %(topic)s"),
                          link_path=lambda e: h.entity_url(e.comment))


# The funny thing about this line is: YOU DO NOT SEE IT!
TYPES = filter(lambda n: isinstance(n, NotificationType), map(eval, dir())) 
