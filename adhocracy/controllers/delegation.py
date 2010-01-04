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
        c.scope = get_entity_or_abort(model.Delegateable, id)
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
                    
                    ## make this optional in the UI 
                    log.debug("Replaying the vote for Delegation: %s" % delegation)
                    replay = validators.Int(if_empty=0, if_missing=0, not_empty=False)
                    if replay == 1:
                        for vote in democracy.Decision.replay_decisions(delegation):
                            event.emit(event.T_VOTE_CAST, vote.user, instance=c.instance, 
                                       topics=[vote.poll.motion], vote=vote, poll=vote.poll)
                    
                    event.emit(event.T_DELEGATION_CREATE, c.user, instance=c.instance, 
                               topics=[c.scope], scope=c.scope, agent=agent)
                                       
                    redirect_to("/d/%s" % str(c.scope.id))
            except formencode.validators.Invalid, error:
                errors = error.error_dict
                #pass
        else:
            fillins['agent'] = 'other'
            fillins['replay'] = 1
        return htmlfill.render(render("delegation/create.html"),
                    defaults=fillins, errors=errors)
        
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("vote.cast"))
    def revoke(self, id):
        c.delegation = get_entity_or_abort(model.Delegation, id)
        if not c.delegation.principal == c.user:
            abort(403, _("Cannot access delegation %(id)s") % {'id': id})
        c.delegation.revoke_time = datetime.now()
        
        event.emit(event.T_DELEGATION_REVOKE, c.user, topics=[c.delegation.scope],
                   scope=c.delegation.scope, agent=c.delegation.agent)
        
        model.meta.Session.add(c.delegation)
        model.meta.Session.commit()        
        h.flash(_("The delegation is now revoked."))
        redirect_to("/d/%s" % str(c.delegation.scope.id))
    
    @ActionProtector(has_permission("delegation.view"))
    def review(self, id):
        c.delegation = get_entity_or_abort(model.Delegation, id)
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
        
        
        
    