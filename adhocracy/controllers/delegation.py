from datetime import datetime

from pylons.i18n import _
import formencode.validators

from adhocracy.lib.base import *
import adhocracy.model.forms as forms
from repoze.what.plugins.pylonshq import ActionProtector

log = logging.getLogger(__name__)

class DelegationController(BaseController):
    
    @RequireInstance
    @RequireInternalRequest(methods=["POST"])
    @ActionProtector(has_permission("vote.cast"))
    def create(self):
        id = request.params.get("scope", c.instance.root.id)
        c.scope = model.Delegateable.find(id)
        if not c.scope:
            abort(404, _("No motion or category with ID '%(id)s' exists") % {'id':id})
        errors = {}
        fillins = dict(request.params.items())
        if request.method == "POST":
            try:
                agent = request.params['agent']
                if agent == 'other':
                    agent = request.params['agent_other']
                agent = forms.ExistingUserName().to_python(agent)
                if agent and agent != c.user:
                    delegation = model.Delegation(c.user, agent, c.scope)
                    model.meta.Session.add(delegation)
                    model.meta.Session.commit()
                    
                    log.debug("Replaying the vote for Delegation: %s" % delegation)
                    democracy.Decision.replay_decisions(delegation)
                    
                    event.emit(event.T_DELEGATION_CREATE, {'scope': c.scope, 'agent': agent},
                               c.user, scopes=[c.instance], topics=[c.scope, agent])
                    
                    redirect_to("/d/%s" % str(c.scope.id))
            except formencode.validators.Invalid, error:
                errors = error.error_dict
                #pass
        else:
            fillins['agent'] = 'other'
        return htmlfill.render(render("delegation/create.html"),
                    defaults=fillins, errors=errors)
        
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("vote.cast"))
    def revoke(self, id):
        delegation = model.Delegation.find(id)
        if not delegation:
            abort(404, _("Couldn't find delegation %(id)s") % {'id': id})
        if not delegation.principal == c.user:
            abort(403, _("Cannot access delegation %(id)s") % {'id': id})
        delegation.revoke_time = datetime.now()
        
        event.emit(event.T_DELEGATION_REVOKE, 
                   {'scope': delegation.scope, 'agent': delegation.agent}, c.user,
                   topics=[delegation.scope, delegation.agent])
        
        model.meta.Session.add(delegation)
        model.meta.Session.commit()        
        h.flash(_("The delegation is now revoked."))
        redirect_to("/d/%s" % str(delegation.scope.id))
    
    @ActionProtector(has_permission("delegation.view"))
    def review(self, id):
        c.delegation = model.Delegation.find(id)
        if not c.delegation:
            abort(404, _("Couldn't find delegation %(id)s") % {'id': id})
        c.scope = c.delegation.scope
        
        decisions = democracy.Decision.for_user(c.delegation.principal, c.instance)
        decisions = filter(lambda d: c.delegation in d.delegations, decisions)
        
        c.decisions_pager = NamedPager('decisions', decisions, tiles.decision.user_row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest},
                                    default_sort=sorting.entity_newest)
        
        return render("delegation/review.html")
    
    @RequireInstance
    @ActionProtector(has_permission("user.view"))    
    def graph(self):
        c.users = model.meta.Session.query(model.User).all()
        c.delegations = model.meta.Session.query(model.Delegation).all()
        response.content_type  = "text/plain"
        return render("/delegation/graph.dot")
        
        
        
    