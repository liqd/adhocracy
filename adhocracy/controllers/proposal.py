import cgi
from datetime import datetime

from pylons.i18n import _
from formencode import foreach

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms
from adhocracy.lib.tiles.proposal_tiles import ProposalTile

log = logging.getLogger(__name__)

def not_null(lst):
    return [item for item in lst if item is not None]

class ProposalNewForm(formencode.Schema):
    allow_extra_fields = True
    issue = forms.ValidIssue()
    canonical = foreach.ForEach(validators.String(max=20000, if_empty=None), convert_to_list=True)
    alternative = foreach.ForEach(forms.ValidProposal(if_invalid=None), convert_to_list=True)

class ProposalCreateForm(ProposalNewForm):
    label = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=20000, min=4, not_empty=True)
    
class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True
    alternative = foreach.ForEach(forms.ValidProposal(if_invalid=None), convert_to_list=True)
    
class ProposalUpdateForm(ProposalEditForm):
    label = validators.String(max=255, min=4, not_empty=True)
    issue = forms.ValidIssue(not_empty=True)
    
class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)

class ProposalController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        query = self.form_result.get('proposals_q')
        proposals = []
        if query:
            proposals = libsearch.query.run(query + "*", instance=c.instance, 
                                         entity_type=model.Proposal)
        else:
            proposals = model.Proposal.all(instance=c.instance)
        
        if format == 'json':
            return render_json(proposals)
        
        c.proposals_pager = pager.proposals(proposals, has_query=query is not None)
        c.tile = tiles.instance.InstanceTile(c.instance)
        return render("/proposal/index.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.create"))
    @validate(schema=ProposalNewForm(), form='bad_request', post_only=False, on_get=True)
    def new(self):
        c.issue = self.form_result.get('issue')
        c.proposals = model.Proposal.all(instance=c.instance)
        c.canonicals = not_null(self.form_result.get('canonical'))
        c.canonicals.extend(['', ''][:max(0, 2-len(c.canonicals))])
        c.alternatives = not_null(self.form_result.get('alternative'))
        return render("/proposal/new.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("proposal.create"))
    @validate(schema=ProposalCreateForm(), form='new', post_only=True)
    def create(self):
        c.issue = self.form_result.get('issue')
        proposal = model.Proposal.create(c.instance, self.form_result.get("label"), 
                                         c.user, c.issue)
        comment = model.Comment.create(self.form_result.get('text'), c.user, proposal)
        if h.has_permission('vote.cast'):
            democracy.Decision(c.user, comment.poll).make(model.Vote.YES)
        for c_text in not_null(self.form_result.get('canonical')):
            canonical = model.Comment.create(c_text, c.user, proposal, canonical=True)
            if h.has_permission('vote.cast'):
                democracy.Decision(c.user, canonical.poll).make(model.Vote.YES)
        alternatives = not_null(self.form_result.get('alternative'))
        proposal.update_alternatives(alternatives)
        model.meta.Session.commit()
        proposal.comment = comment
        model.meta.Session.commit()
        watchlist.check_watch(proposal)
        event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance, 
                   topics=[proposal], proposal=proposal)
        redirect_to("/proposal/%s" % proposal.id)


    @RequireInstance
    @ActionProtector(has_permission("proposal.edit")) 
    @validate(schema=ProposalEditForm(), form="bad_request", post_only=False, on_get=True)
    def edit(self, id):
        c.proposal = self._get_mutable_proposal(id)
        if 'alternative' in request.params:
            c.alternatives = not_null(self.form_result.get('alternative'))
        else: 
            c.alternatives = c.proposal.current_alternatives()
        c.issues = model.Issue.all(instance=c.instance)
        c.proposals = model.Proposal.all(instance=c.instance)
        return render("/proposal/edit.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("proposal.edit")) 
    @validate(schema=ProposalUpdateForm(), form="edit", post_only=True)
    def update(self, id):
        proposal = self._get_mutable_proposal(id)
        proposal.label = self.form_result.get("label")
        proposal.issue = self.form_result.get("issue")
        alternatives = not_null(self.form_result.get('alternative'))
        proposal.update_alternatives(alternatives)
        model.meta.Session.commit()
        watchlist.check_watch(proposal)
        event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance, 
                   topics=[proposal], proposal=proposal)
        redirect_to("/proposal/%s" % proposal.id)
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    def show(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)     
        
        if format == 'rss':
            return self.activity(id, format)
        
        if format == 'json':
            return render_json(c.proposal)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        c.issue_tile = tiles.issue.IssueTile(c.proposal.issue)
        self._common_metadata(c.proposal)
        return render("/proposal/show.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    def delegations(self, id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        delegations = c.proposal.current_delegations()
        
        if format == 'json':
            return render_json(list(delegations))
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        c.delegations_pager = pager.delegations(delegations)
        self._common_metadata(c.proposal)
        return render("/proposal/delegations.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    def canonicals(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        
        if format == 'json':
            return render_json(c.proposal.canonicals)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        self._common_metadata(c.proposal)
        return render("/proposal/canonicals.html")

    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    def alternatives(self, id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        alternatives = c.proposal.current_alternatives()
        
        if format == 'json':
            return render_json(alternatives)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        c.proposals_pager = pager.proposals(alternatives)
        self._common_metadata(c.proposal)
        return render("/proposal/alternatives.html")
    

    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    def activity(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        events = model.Event.find_by_topic(c.proposal)
        
        if format == 'rss':
            return event.rss_feed(events, _("Proposal: %s") % c.proposal.label,
                                  h.instance_url(c.instance, path="/proposal/%s" % c.proposal.id),
                                  description=_("Activity on the %s proposal") % c.proposal.label)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        c.events_pager = pager.events(events)
        self._common_metadata(c.proposal)
        return render("/proposal/activity.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.delete"))
    def ask_delete(self, id):
        c.proposal = self._get_mutable_proposal(id)
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        return render('/proposal/ask_delete.html')
    
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("proposal.delete"))
    def delete(self, id):
        c.proposal = self._get_mutable_proposal(id)
        event.emit(event.T_PROPOSAL_DELETE, c.user, instance=c.instance, 
                   topics=[c.proposal], proposal=c.proposal)
        c.proposal.delete()
        model.meta.Session.commit()
        redirect_to(h.entity_url(c.proposal.issue))   
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view")) 
    def adopted(self):
        issues = model.Issue.all(instance=c.instance)
        c.issues = sorting.delegateable_label(issues)
        return render("/proposal/adopted.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("poll.create"))
    def ask_adopt(self, id):
        c.proposal = self._get_mutable_proposal(id)
        if not c.proposal.can_adopt():
            abort(403, _("The poll cannot be started either because there are " + 
                         "no provisions or a poll has already started."))
        return render('/proposal/ask_adopt.html')
        
    
    @RequireInstance
    @ActionProtector(has_permission("poll.create"))
    def adopt(self, id):
        c.proposal = self._get_mutable_proposal(id)
        if not c.proposal.can_adopt():
            abort(403, _("The poll cannot be started either because there are " + 
                         "no provisions or a poll has already started."))
        poll = model.Poll.create(c.proposal, c.user, model.Poll.ADOPT)
        model.meta.Session.commit()
        c.proposal.adopt_poll = poll 
        model.meta.Session.commit()
        event.emit(event.T_PROPOSAL_STATE_VOTING, c.user, instance=c.instance, 
                   topics=[c.proposal], proposal=c.proposal, poll=poll)
        redirect_to(h.entity_url(c.proposal))   
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def filter(self):
        query = self.form_result.get('proposals_q')
        if query is None: query = ''
        proposals = libsearch.query.run(query + "*", instance=c.instance, 
                                     entity_type=model.Proposal)
        c.proposals_pager = pager.proposals(proposals, has_query=True)
        return c.proposals_pager.here()
    
    
    def _get_mutable_proposal(self, id):
        proposal = get_entity_or_abort(model.Proposal, id)
        if not proposal.is_mutable():
            abort(403, h.immutable_proposal_message())
        return proposal
    
    
    def _common_metadata(self, proposal):
        h.add_meta("description", 
                   text.meta_escape(proposal.comment.latest.text, markdown=False)[0:160])
        h.add_meta("dc.title", 
                   text.meta_escape(proposal.label, markdown=False))
        h.add_meta("dc.date", 
                   proposal.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", 
                   text.meta_escape(proposal.creator.name, markdown=False))
        h.add_rss(_("Proposal: %(proposal)s") % {'proposal': proposal.label}, 
                  h.instance_url(c.instance, "/proposal/%s.rss" % proposal.id))
