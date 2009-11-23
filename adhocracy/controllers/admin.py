from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *

from adhocracy.model.forms import AdminUpdateMembershipForm, AdminForceLeaveForm

log = logging.getLogger(__name__)

class AdminController(BaseController):

    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("global.admin"))
    def permissions(self):
        if request.method == "POST":
            groups = model.Group.all()
            for permission in model.Permission.all():
                for group in groups:
                    t = request.params.get("%s-%s" % (
                            group.code, permission.permission_name))
                    if t and permission not in group.permissions:
                        group.permissions.append(permission)
                    elif not t and permission in group.permissions:
                        group.permissions.remove(permission)
            for group in groups:
                model.meta.Session.add(group)
            model.meta.Session.commit()
        return render("/admin/permissions.html")
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("instance.admin"))
    def members(self):
        return render("/admin/members.html")
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.admin"))
    @validate(schema=AdminUpdateMembershipForm(), form="members", post_only=False, on_get=True)
    def update_membership(self):
        user = self.form_result.get("user")
        to_group = self.form_result.get("to_group")
        if not to_group.code in [model.Group.CODE_OBSERVER, 
                                 model.Group.CODE_VOTER, 
                                 model.Group.CODE_SUPERVISOR]:
            h.flash("Cannot make %(user)s a member of %(group)s" % {
                        'user': user.name, 
                        'group': group.group_name})
            return render("/admin/members.html")
        
        had_vote = True if user.has_permission("vote.cast") else False
        
        for membership in user.memberships:
            if not membership.expire_time and membership.instance == c.instance:
                membership.group = to_group
                model.meta.Session.add(membership)
                model.meta.Session.commit()
                
                event.emit(event.T_INSTANCE_MEMBERSHIP_UPDATE, user, 
                           scopes=[c.instance], topics=[c.page_instance, user],
                           group=to_group.code, instance=c.instance)
                
                if had_vote and not user.has_permission("vote.cast"):
                    # user has lost voting privileges
                    democracy.DelegationNode.detach(user, c.instance)
                
                redirect_to("/admin/members#u_%s" % str(user.user_name))
        h.flash(_("%(user)s is not a member of %(instance)s") % {
                        'user': user.name, 
                        'instance': c.instance.label})
        return render("/admin/members.html")
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.admin"))
    @validate(schema=AdminForceLeaveForm(), form="members", post_only=False, on_get=True)
    def force_leave(self):
        user = self.form_result.get("user")
        for membership in user.memberships:
            if not membership.expire_time and membership.instance == c.instance:
                membership.expire_time = datetime.now()
                model.meta.Session.add(membership)
                model.meta.Session.commit()
                
                democracy.DelegationNode.detach(user, c.instance)
                
                event.emit(event.T_INSTANCE_FORCE_LEAVE, user, scopes=[c.instance], 
                           topics=[c.page_instance, user, c.user], instance=c.instance, 
                           user=c.user)
                
                h.flash(_("%(user)s was removed from %(instance)s") % {
                                'user': user.name, 
                                'instance': c.instance.label})
                return render("/admin/members.html")
        h.flash(_("%(user)s isn't a member of %(instance)s") % {
                        'user': user.name, 
                        'instance': c.instance.label})
        return render("/admin/members.html")

