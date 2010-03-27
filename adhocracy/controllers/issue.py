import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import * 
from adhocracy.lib.base import BaseController, render
import adhocracy.model.forms as forms
import adhocracy.lib.text as text

log = logging.getLogger(__name__)

class IssueCreateForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=10000, not_empty=False, if_empty="")

class IssueEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    
class IssueFilterForm(formencode.Schema):
    allow_extra_fields = True
    issues_q = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)

class IssueController(BaseController):

    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    @validate(schema=IssueFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        query = self.form_result.get('issues_q')
        issues = []
        if query:
            issues = libsearch.query.run(query + "*", instance=c.instance, 
                                         entity_type=model.Issue)
        else:
            issues = model.Issue.all(instance=c.instance)
        
        if format == 'json':
            return render_json(issues)
        
        c.issues_pager = pager.issues(issues, has_query=query is not None)
        c.tile = tiles.instance.InstanceTile(c.instance)
        return render("/issue/index.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.create"))
    def new(self):
        return render("/issue/new.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("issue.create"))
    @validate(schema=IssueCreateForm(), form="new", post_only=True)
    def create(self):
        issue = model.Issue.create(c.instance, self.form_result.get('label'), 
                                   c.user)
        comment = model.Comment.create(self.form_result.get('text'), c.user, issue)
        if h.has_permission('vote.cast'):
            decision = democracy.Decision(c.user, comment.poll).make(model.Vote.YES)
        model.meta.Session.commit()
        issue.comment = comment
        model.meta.Session.commit()
        watchlist.check_watch(issue)
        event.emit(event.T_ISSUE_CREATE, c.user, instane=c.instance, 
                   topics=[issue], issue=issue, rev=comment.latest)
        redirect(h.entity_url(issue))
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.edit"))
    def edit(self, id):
        c.issue = get_entity_or_abort(model.Issue, id)
        return render("/issue/edit.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("issue.edit"))
    @validate(schema=IssueEditForm(), form="edit", post_only=True)
    def update(self, id):
        c.issue = get_entity_or_abort(model.Issue, id)
        c.issue.label = self.form_result.get('label')
        model.meta.Session.add(c.issue)
        model.meta.Session.commit()        
        watchlist.check_watch(c.issue)
        event.emit(event.T_ISSUE_EDIT, c.user, instance=c.instance, 
                   topics=[c.issue], issue=c.issue, rev=c.issue.comment.latest)
        redirect(h.entity_url(c.issue))
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def show(self, id, format="html"):
        c.issue = get_entity_or_abort(model.Issue, id)
        if format == 'rss':
            return self.activity(id, format)      
        return self.discussion(id, format)
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def discussion(self, id, format='html'):
        c.issue = get_entity_or_abort(model.Issue, id)
        
        if format == 'json':
            return render_json(c.issue.comments)
        
        c.tile = tiles.issue.IssueTile(c.issue)
        self._common_metadata(c.issue)
        return render("/issue/discussion.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def activity(self, id, format='html'):
        c.issue = get_entity_or_abort(model.Issue, id)
        
        if format == 'sline':
            sline = event.sparkline_samples(event.issue_activity, c.issue)
            return render_json(dict(activity=sline))
        
        events = model.Event.find_by_topics([c.issue] + c.issue.proposals)
        
        if format == 'rss':
            return event.rss_feed(events, _("Issue: %s") % c.issue.label,
                                  h.instance_url(c.instance, path="/issue/%s" % str(c.issue.id)),
                                  description=_("Activity on the %s issue") % c.issue.label)
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.events_pager = pager.events(events)
        self._common_metadata(c.issue)
        return render("/issue/activity.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def proposals(self, id, format="html"):
        c.issue = get_entity_or_abort(model.Issue, id)
        
        if format == 'json':
            return render_json(c.issue.proposals)
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.proposals_pager = pager.proposals(c.issue.proposals, detail=True)
        self._common_metadata(c.issue)
        return render("/issue/proposals.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def delegations(self, id, format="html"):
        c.issue = get_entity_or_abort(model.Issue, id)
        delegations = c.issue.current_delegations()
        
        if format == 'json':
            return render_json(list(delegations))
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.delegations_pager = pager.delegations(delegations)
        self._common_metadata(c.issue)
        return render("/issue/delegations.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.delete"))
    def ask_delete(self, id):
        c.issue = get_entity_or_abort(model.Issue, id)
        c.tile = tiles.issue.IssueTile(c.issue)
        return render("/issue/ask_delete.html")
        
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("issue.delete"))
    def delete(self, id):
        c.issue = get_entity_or_abort(model.Issue, id)        
        for proposal in c.issue.proposals:
            if not proposal.is_mutable():
                h.flash(_("The issue %(issue)s cannot be deleted, because the contained " +
                          "proposal %(proposal)s is polling.") % {'issue': c.issue.label, 'proposal': proposal.label})
                redirect(h.entity_url(c.issue))
        c.issue.delete()
        model.meta.Session.commit()
        event.emit(event.T_ISSUE_DELETE, c.user, instance=c.instance, 
                   topics=[c.issue], issue=c.issue)
        h.flash(_("The issue %s has been deleted.") % c.issue.label)
        redirect(h.entity_url(c.issue.instance))
        
        
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    @validate(schema=IssueFilterForm(), post_only=False, on_get=True)
    def filter(self):
        query = self.form_result.get('issues_q')
        if query is None: query = ''
        issues = libsearch.query.run(query + "*", instance=c.instance, 
                                     entity_type=model.Issue)
        c.issues_pager = pager.issues(issues, has_query=True)
        return c.issues_pager.here()
     
    
    def _common_metadata(self, issue):
        h.add_meta("dc.title", text.meta_escape(issue.label, markdown=False))
        h.add_meta("dc.date", issue.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", text.meta_escape(issue.creator.name, markdown=False))
        
        h.add_rss(_("Issue: %(issue)s") % {'issue': issue.label}, 
                    h.entity_url(c.issue, format='rss'))

