from datetime import datetime

from pylons.i18n import _
import formencode.validators
import formencode.foreach
from formencode.validators import RequireIfMissing

from adhocracy.lib.base import *
import adhocracy.model.forms as forms
from repoze.what.plugins.pylonshq import ActionProtector

log = logging.getLogger(__name__)

class DelegationNewForm(formencode.Schema):
    allow_extra_fields = True
    scope = forms.ValidDelegateable()

class DelegationCreateForm(DelegationNewForm):
    agent = formencode.foreach.ForEach(forms.ExistingUserName())
    replay = validators.Int(if_empty=1, if_missing=1, not_empty=False)

class DelegationController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("delegation.view"))
    def index(self, format='html'):
        c.delegations = model.Delegation.all(instance=c.instance)
        if format == 'dot':
            c.users = model.User.all(instance=c.instance)
            response.content_type  = "text/plain"
            return render("/delegation/graph.dot")
        if format == 'json':
            return render_json(c.delegations)
        return self.not_implemented()
    
    @RequireInstance
    @ActionProtector(has_permission("vote.cast"))
    @validate(schema=DelegationNewForm(), form="bad_request", 
              post_only=False, on_get=True)
    def new(self):
        c.scope = self.form_result.get('scope')
        return render("/delegation/new.html")
    
    @RequireInstance
    @RequireInternalRequest(methods=["POST"])
    @ActionProtector(has_permission("vote.cast"))
    @validate(schema=DelegationCreateForm(), form="new", post_only=True)
    def create(self):
        c.scope = self.form_result.get('scope')
        agents = filter(lambda f: f is not None, self.form_result.get('agent'))
        if not len(agents) or agents[0] == c.user:
            h.flash(_("Invalid delegation recipient"))
            return self.new()
        
        existing = model.Delegation.find_by_agent_principal_scope(agents[0],
                                                                  c.user,
                                                                  c.scope)
        if existing is not None:
            h.flash(_("You have already delegated voting to %s in %s") % (agents[0], c.scope))
            return self.new()
        
        delegation = c.user.delegate_to_user_in_scope(agents[0], c.scope)
        model.meta.Session.commit()
        
        event.emit(event.T_DELEGATION_CREATE, c.user, 
                   instance=c.instance, 
                   topics=[c.scope], scope=c.scope, 
                   agent=agents[0])
        
        if self.form_result.get('replay') == 1:
            log.debug("Replaying the vote for Delegation: %s" % delegation)
            for vote in democracy.Decision.replay_decisions(delegation):
                event.emit(event.T_VOTE_CAST, vote.user, 
                           instance=c.instance, 
                           topics=[vote.poll.proposal], 
                           vote=vote, poll=vote.poll)
        
        redirect_to("/d/%s" % str(c.scope.id))
        
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("vote.cast"))
    def delete(self, id):
        c.delegation = get_entity_or_abort(model.Delegation, id)
        if not c.delegation.principal == c.user:
            abort(403, _("Cannot access delegation %(id)s") % {'id': id})
        c.delegation.revoke()
        model.meta.Session.commit()
        event.emit(event.T_DELEGATION_REVOKE, c.user, topics=[c.delegation.scope],
                   scope=c.delegation.scope, instance=c.instance, agent=c.delegation.agent)        
        h.flash(_("The delegation is now revoked."))
        redirect_to("/d/%s" % str(c.delegation.scope.id))
    
    @ActionProtector(has_permission("delegation.view"))
    def show(self, id, format='html'):
        c.delegation = get_entity_or_abort(model.Delegation, id)
        c.scope = c.delegation.scope
        
        if format == 'json':
            return render_json(c.delegation)
        
        decisions = democracy.Decision.for_user(c.delegation.principal, c.instance)
        decisions = filter(lambda d: c.delegation in d.delegations, decisions)
        
        c.decisions_pager = NamedPager('decisions', decisions, tiles.decision.user_row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest},
                                    default_sort=sorting.entity_newest)
        
        return render("delegation/show.html")
    
    @RequireInstance
    @ActionProtector(has_permission("delegation.view"))
    def edit(self, format='html'):
        return self.not_implemented()
    
    @RequireInstance
    @ActionProtector(has_permission("delegation.view"))
    def update(self, format='html'):
        return self.not_implemented()
    