import cgi
from datetime import datetime

from pylons.i18n import _
from formencode import foreach, Invalid
from sqlalchemy import or_, and_
from sqlalchemy.orm import eagerload_all, eagerload

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.forms as forms
from adhocracy.lib.tiles.proposal_tiles import ProposalTile

log = logging.getLogger(__name__)

class ProposalNewForm(formencode.Schema):
    allow_extra_fields = True

class ProposalCreateForm(ProposalNewForm):
    label = forms.UnusedTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    tags = validators.String(max=20000, not_empty=False)
    
class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True
    
class ProposalUpdateForm(ProposalEditForm):
    label = forms.UnusedTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    
class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False, if_empty=u'', if_missing=u'')
    proposals_state = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)


class ProposalController(BaseController):
    
    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        require.proposal.index()
        query = self.form_result.get('proposals_q')
        proposals = libsearch.query.run(query + u"*", instance=c.instance, 
                                        entity_type=model.Proposal)
        
        if self.form_result.get('proposals_state'):
            proposals = model.Proposal.filter_by_state(self.form_result.get('proposals_state'), 
                                                       proposals)
        c.proposals_pager = pager.proposals(proposals)
        
        if format == 'json':
            return render_json(c.proposals_pager)
        
        tags = model.Tag.popular_tags(limit=30)
        c.cloud_tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, c, v): k.name)
        
        c.tile = tiles.instance.InstanceTile(c.instance)
        return render("/proposal/index.html")
    
    
    @RequireInstance
    @validate(schema=ProposalNewForm(), form='bad_request', post_only=False, on_get=True)
    def new(self, errors=None):
        require.proposal.create()
        defaults = dict(request.params)
        defaults['watch'] = defaults.get('watch', True)
        return htmlfill.render(render("/proposal/new.html"), defaults=defaults, 
                               errors=errors, force_defaults=False)
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    def create(self, format='html'):
        require.proposal.create()
        try:
            self.form_result = ProposalCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors())
        proposal = model.Proposal.create(c.instance, self.form_result.get("label"), 
                                         c.user, with_vote=can.user.vote(),
                                         tags=self.form_result.get("tags"))
        model.meta.Session.flush()
        description = model.Page.create(c.instance, self.form_result.get("label"), 
                                        self.form_result.get('text'), c.user, 
                                        function=model.Page.DESCRIPTION)
        description.parents = [proposal]
        model.meta.Session.flush()
        proposal.description = description
        model.meta.Session.commit()
        text.clear_render_cache()
        watchlist.check_watch(proposal)
        event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance, 
                   topics=[proposal], proposal=proposal, rev=description.head)
        redirect(h.entity_url(proposal, format=format))


    @RequireInstance
    @validate(schema=ProposalEditForm(), form="bad_request", post_only=False, on_get=True)
    def edit(self, id, errors={}):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.edit(c.proposal)
        c.text_rows = text.text_rows(c.proposal.description.head)
        return htmlfill.render(render("/proposal/edit.html"), defaults=dict(request.params), 
                               errors=errors, force_defaults=False)
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    def update(self, id, format='html'):
        try:
            c.proposal = get_entity_or_abort(model.Proposal, id)
            class state_(object):
                page = c.proposal.description
            self.form_result = ProposalUpdateForm().to_python(request.params, 
                                                              state=state_())
        except Invalid, i:
            return self.edit(id, errors=i.unpack_errors())
        
        require.proposal.edit(c.proposal)
        
        c.proposal.label = self.form_result.get('label')
        model.meta.Session.add(c.proposal)
        _text = model.Text.create(c.proposal.description, model.Text.HEAD, c.user, 
                                 self.form_result.get('label'), 
                                 self.form_result.get('text'), 
                                 parent=c.proposal.description.head)
        model.meta.Session.commit()
        text.clear_render_cache()
        watchlist.check_watch(c.proposal)
        event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance, 
                   topics=[c.proposal], proposal=c.proposal, rev=_text)
        redirect(h.entity_url(c.proposal))
    
    
    @RequireInstance
    def show(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)
        
        #q = model.meta.Session.query(model.Proposal)
        #id = int(unicode(id).split('-', 1)[0])
        #q = q.filter(model.Proposal.id==id)
        #q = q.filter(model.Proposal.instance_id==c.instance.id)
        #q = q.filter(or_(model.Proposal.delete_time==None,
        #                 model.Proposal.delete_time>datetime.utcnow()))
        #q = q.options(eagerload_all('parents'))
        #q = q.options(eagerload_all('rate_poll.tallies'))
        #q = q.options(eagerload_all('creator'))
        #q = q.options(eagerload_all('rate_poll.tallies'))
        #q = q.options(eagerload_all('taggings'))
        #q = q.options(eagerload_all('description'))
        #q = q.options(eagerload_all('description.creator'))
        #q = q.options(eagerload_all('description.comments.revisions'))
        #q = q.options(eagerload_all(model.Proposal._selections))
        #q = q.options(eagerload_all('_selections.page._texts'))
        #q = q.options(eagerload_all('children'))
        #q = q.options(eagerload_all('parents'))
        #c.proposal = q.first()
        
        if format == 'rss':
            return self.activity(id, format)
        
        if format == 'json':
            return render_json(c.proposal)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        self._common_metadata(c.proposal)
        return render("/proposal/show.html")
    
    
    @RequireInstance
    def delegations(self, id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)
        delegations = c.proposal.current_delegations()
        c.delegations_pager = pager.delegations(delegations)
        
        if format == 'json':
            return render_json(c.delegations_pager)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        self._common_metadata(c.proposal)
        return render("/proposal/delegations.html")
    
        
    @RequireInstance
    def contributors(self, id, format="html"):
        # TODO: use my own pager here
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)
        contributors = [user for (user, score) in c.proposal.contributors()]
        c.users_pager = pager.users(contributors)

        if format == 'json':
            return render_json(c.users_pager)

        c.tile = tiles.proposal.ProposalTile(c.proposal)
        self._common_metadata(c.proposal)
        return render("/proposal/contributors.html")
    

    @RequireInstance
    def activity(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)
        events = model.Event.find_by_topic(c.proposal)
        
        if format == 'rss':
            return event.rss_feed(events, _("Proposal: %s") % c.proposal.title,
                                  h.entity_url(c.proposal),
                                  description=_("Activity on the %s proposal") % c.proposal.title)
        
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        c.events_pager = pager.events(events)
        self._common_metadata(c.proposal)
        return render("/proposal/activity.html")
    
    
    @RequireInstance
    def ask_delete(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.delete(c.proposal)
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        return render('/proposal/ask_delete.html')
    
    
    @RequireInstance
    @RequireInternalRequest()
    def delete(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.delete(c.proposal)
        event.emit(event.T_PROPOSAL_DELETE, c.user, instance=c.instance, 
                   topics=[c.proposal], proposal=c.proposal)
        c.proposal.delete()
        model.meta.Session.commit()
        text.clear_render_cache()
        h.flash(_("The proposal %s has been deleted.") % c.proposal.title)
        redirect(h.entity_url(c.instance))   
    
    
    @RequireInstance
    def ask_adopt(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.adopt(c.proposal)
        return render('/proposal/ask_adopt.html')
        
    
    @RequireInstance
    def adopt(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.adopt(c.proposal)
        poll = model.Poll.create(c.proposal, c.user, model.Poll.ADOPT)
        model.meta.Session.commit()
        c.proposal.adopt_poll = poll 
        model.meta.Session.commit()
        event.emit(event.T_PROPOSAL_STATE_VOTING, c.user, instance=c.instance, 
                   topics=[c.proposal], proposal=c.proposal, poll=poll)
        redirect(h.entity_url(c.proposal))   
    
    
    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def filter(self):
        require.proposal.index()
        query = self.form_result.get('proposals_q', u'')
        proposals = libsearch.query.run(query + u"*", instance=c.instance, 
                                     entity_type=model.Proposal)
        c.proposals_pager = pager.proposals(proposals)
        return c.proposals_pager.here()
       
    
    def _common_metadata(self, proposal):
        h.add_meta("description", 
                   text.meta_escape(proposal.description.head.text, markdown=False)[0:160])
        tags = proposal.tags
        if len(tags):
            h.add_meta("keywords", ", ".join([k.name for (k, v) in tags]))
        h.add_meta("dc.title", 
                   text.meta_escape(proposal.title, markdown=False))
        h.add_meta("dc.date", 
                   proposal.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", 
                   text.meta_escape(proposal.creator.name, markdown=False))
        h.add_rss(_("Proposal: %(proposal)s") % {'proposal': proposal.title}, 
                  h.entity_url(c.proposal, format='rss'))
