from pylons.i18n import _

T_USER_CREATE = u"t_account_create"
T_USER_EDIT = u"t_account_edit"
T_USER_ADMIN_EDIT = u"t_account_admin_edit"

T_INSTANCE_CREATE = u"t_instance_create"
T_INSTANCE_EDIT = u"t_instance_edit"
T_INSTANCE_DELETE = u"t_instance_delete"
T_INSTANCE_JOIN = u"t_instance_join"
T_INSTANCE_LEAVE = u"t_instance_leave"
T_INSTANCE_FORCE_LEAVE = u"t_instance_force_leave"
T_INSTANCE_MEMBERSHIP_UPDATE = u"t_instance_membership_update"

T_ISSUE_CREATE = u"t_issue_create"
T_ISSUE_EDIT = u"t_issue_edit"
T_ISSUE_DELETE = u"t_issue_delete"

T_MOTION_CREATE = u"t_motion_create"
T_MOTION_EDIT = u"t_motion_edit"
T_MOTION_STATE_REDRAFT = u"t_motion_state_draft"
T_MOTION_STATE_VOTING = u"t_motion_state_voting"
T_MOTION_DELETE = u"t_motion_delete"

T_EDITOR_ADD = u"t_editor_add"
T_EDITOR_REMOVE = u"t_editor_remove"

T_CATEGORY_CREATE = u"t_category_create"
T_CATEGORY_EDIT = u"t_category_edit"
T_CATEGORY_DELETE = u"t_category_delete"

T_COMMENT_CREATE = u"t_comment_create"
T_COMMENT_EDIT = u"t_comment_edit"
T_COMMENT_DELETE = u"t_comment_delete"

T_DELEGATION_CREATE = u"t_delegation_create"
T_DELEGATION_REVOKE = u"t_delegation_revoke"

T_VOTE_CAST = u"t_vote_cast"

T_TEST = u"t_test"

messages = {
    T_USER_CREATE: lambda: _(u"signed up"),
    T_USER_EDIT: lambda: _(u"edited their profile"),
    T_USER_ADMIN_EDIT: lambda: _(u"edited %(user)ss profile"),
    T_INSTANCE_CREATE: lambda: _(u"founded the %(instance)s Adhocracy"),
    T_INSTANCE_EDIT: lambda: _(u"updated the %(instance)s Adhocracy"),
    T_INSTANCE_DELETE: lambda: _(u"deleted the %(instance)s Adhocracy"),
    T_INSTANCE_JOIN: lambda: _(u"joined %(instance)s"),
    T_INSTANCE_LEAVE: lambda: _(u"left %(instance)s"),
    T_INSTANCE_FORCE_LEAVE: lambda: _(u"was forced to leave %(instance)s by %(user)s"),
    T_INSTANCE_MEMBERSHIP_UPDATE: lambda: _(u"now is a %(group)s within %(instance)s"),
    T_ISSUE_CREATE: lambda: _(u"created %(issue)s"),
    T_ISSUE_EDIT: lambda: _(u"edited %(issue)s"),
    T_ISSUE_DELETE: lambda: _(u"deleted %(issue)s"),
    T_MOTION_CREATE: lambda: _(u"created %(motion)s"),
    T_MOTION_EDIT: lambda: _(u"edited %(motion)s"),
    T_MOTION_STATE_REDRAFT: lambda: _(u"re-drafted %(motion)s"),
    T_MOTION_STATE_VOTING: lambda: _(u"called a vote on %(motion)s"),
    T_MOTION_DELETE: lambda: _(u"deleted %(motion)s"),
    T_EDITOR_ADD: lambda: _(u"named %(user)s as an editor for %(motion)s"),
    T_EDITOR_REMOVE: lambda: _(u"removed %(user)s from the editors of %(motion)s"),
    T_CATEGORY_CREATE: lambda: _(u"created the category %(category)s in %(parent)s"),
    T_CATEGORY_EDIT: lambda: _(u"updated the category %(category)s"),
    T_CATEGORY_DELETE: lambda: _(u"deleted the category %(category)s"),
    T_COMMENT_CREATE: lambda: _(u"created a %(comment)s on %(delegateable)s"),
    T_COMMENT_EDIT: lambda: _(u"edited a %(comment)s on %(delegateable)s"),
    T_COMMENT_DELETE: lambda: _(u"deleted a %(comment)s from %(delegateable)s"),
    T_DELEGATION_CREATE: lambda: _(u"delegated voting on %(scope)s to %(agent)s"),
    T_DELEGATION_REVOKE: lambda: _(u"revoked their delegation on %(scope)s to %(agent)s"),
    T_VOTE_CAST: lambda: _(u"%(vote)s %(motion)s"),
    T_TEST: lambda: _(u"test %(test)s")
    }
