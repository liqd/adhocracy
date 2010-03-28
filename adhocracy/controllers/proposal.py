import cgi
from datetime import datetime

from pylons.i18n import _
from formencode import foreach, Invalid

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms
from adhocracy.lib.tiles.proposal_tiles import ProposalTile

log = logging.getLogger(__name__)

def not_null(lst):
    return [item for item in lst if item is not None]

class ProposalNewForm(formencode.Schema):
    allow_extra_fields = True
    canonical = foreach.ForEach(validators.String(max=20000, if_empty=None), convert_to_list=True)
    alternative = foreach.ForEach(forms.ValidProposal(if_invalid=None), convert_to_list=True)

class ProposalCreateForm(ProposalNewForm):
    label = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=20000, min=4, not_empty=True)
    tags = validators.String(max=20000, not_empty=False)
    
class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True
    alternative = foreach.ForEach(forms.ValidProposal(if_invalid=None), convert_to_list=True)
    
class ProposalUpdateForm(ProposalEditForm):
    label = validators.String(max=255, min=4, not_empty=True)
    
class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False, if_empty=u'', if_missing=u'')
    proposals_state = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)
    
class ProposalTagCreateForm(formencode.Schema):
    allow_extra_fields = True
    tags = validators.String(max=10000, not_empty=True)

class ProposalTagDeleteForm(formencode.Schema):
    allow_extra_fields = True
    tagging = forms.ValidTagging()


class ProposalController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        query = self.form_result.get('proposals_q')
        proposals = libsearch.query.run(query + u"*", instance=c.instance, 
                                        entity_type=model.Proposal)
        
        if self.form_result.get('proposals_state'): 
            proposals = model.Proposal.filter_by_state(self.form_result.get('proposals_state'), 
                                                       proposals)
        c.proposals_pager = pager.proposals(proposals, has_query=query is not None)
        
        if format == 'json':
            return render_json(c.proposals_pager)
        
        tags = model.Tag.popular_tags(limit=50)
        c.cloud_tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, c, v): k.name)
        
        c.tile = tiles.instance.InstanceTile(c.instance)
        return render("/proposal/index.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.create"))
    @validate(schema=ProposalNewForm(), form='bad_request', post_only=False, on_get=True)
    def new(self, errors=None):
        defaults = dict(request.params)
        c.alternatives = not_null(self.form_result.get('alternative'))
        if len(c.alternatives):
            del defaults['alternative']
        c.proposals = model.Proposal.all(instance=c.instance)
        return htmlfill.render(render("/proposal/new.html"), defaults=defaults, 
                               errors=errors, force_defaults=False)
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("proposal.create"))
    def create(self):
        try:
            self.form_result = ProposalCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors())
        proposal = model.Proposal.create(c.instance, self.form_result.get("label"), 
                                         c.user, with_vote=h.has_permission('vote.cast'),
                                         tags=self.form_result.get("tags"))
        model.meta.Session.commit()
        comment = model.Comment.create(self.form_result.get('text'), 
                                       c.user, proposal, 
                                       with_vote=h.has_permission('vote.cast'))
        alternatives = not_null(self.form_result.get('alternative'))
        proposal.update_alternatives(alternatives)
        model.meta.Session.commit()
        proposal.comment = comment
        model.meta.Session.commit()
        watchlist.check_watch(proposal)
        event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance, 
                   topics=[proposal], proposal=proposal, rev=comment.latest)
        redirect(h.entity_url(proposal))


    @RequireInstance
    @ActionProtector(has_permission("proposal.edit")) 
    @validate(schema=ProposalEditForm(), form="bad_request", post_only=False, on_get=True)
    def edit(self, id, errors={}):
        c.proposal = self._get_mutable_proposal(id)
        defaults = dict(request.params)
        if 'alternative' in request.params:
            c.alternatives = not_null(self.form_result.get('alternative'))
            del defaults['alternative']
        else: 
            c.alternatives = c.proposal.current_alternatives()
        c.proposals = [p for p in model.Proposal.all(instance=c.instance) if not \
                       (p in c.alternatives and not p == c.proposal)]
        return htmlfill.render(render("/proposal/edit.html"), defaults=defaults, 
                               errors=errors, force_defaults=False)
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("proposal.edit")) 
    def update(self, id):
        try:
            self.form_result = ProposalUpdateForm().to_python(request.params)
        except Invalid, i:
            return self.edit(errors=i.unpack_errors())
        proposal = self._get_mutable_proposal(id)
        proposal.label = self.form_result.get("label")
        model.meta.Session.commit()
        alternatives = not_null(self.form_result.get('alternative'))
        proposal.update_alternatives(alternatives)
        model.meta.Session.commit()
        watchlist.check_watch(proposal)
        event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance, 
                   topics=[proposal], proposal=proposal, rev=proposal.comment.latest)
        redirect(h.entity_url(proposal))
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    def show(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)     
        
        if format == 'rss':
            return self.activity(id, format)
        
        if format == 'json':
            return render_json(c.proposal)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
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
        
        if format == 'sline':
            sline = event.sparkline_samples(event.proposal_activity, c.proposal)
            return render_json(dict(activity=sline))
        
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
        h.flash(_("The proposal %s has been deleted.") % c.proposal.label)
        redirect(h.entity_url(c.instance))   
    
    
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
        redirect(h.entity_url(c.proposal))   
    
    
    @RequireInstance
    @ActionProtector(has_permission("proposal.view"))
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def filter(self):
        query = self.form_result.get('proposals_q')
        if query is None: query = u''
        proposals = libsearch.query.run(query + u"*", instance=c.instance, 
                                     entity_type=model.Proposal)
        c.proposals_pager = pager.proposals(proposals, has_query=True)
        return c.proposals_pager.here()
        
        
    @RequireInstance
    @ActionProtector(has_permission("tag.create"))
    @validate(schema=ProposalTagCreateForm(), form="bad_request", post_only=False, on_get=True)
    def tag(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        for tag_text in text.tag_split(self.form_result.get('tags')):
            if not model.Tagging.find_by_delegateable_name_creator(c.proposal, tag_text, c.user):
                tagging = model.Tagging.create(c.proposal, tag_text, c.user)
        model.meta.Session.commit()
        redirect(h.entity_url(c.proposal))
        
        
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("tag.delete"))
    @validate(schema=ProposalTagDeleteForm(), form="bad_request", post_only=False, on_get=True)
    def untag(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        tagging = self.form_result.get('tagging')
        if not tagging.delegateable == c.proposal:
            abort(401, _("Tag does not belong to this proposal."))
        tagging.delete()
        model.meta.Session.commit()
        redirect(h.entity_url(c.proposal))
    
    
    def _get_mutable_proposal(self, id):
        proposal = get_entity_or_abort(model.Proposal, id, full=True)
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
                  h.entity_url(c.proposal, format='rss'))
