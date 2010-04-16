import logging
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import * 
from adhocracy.lib.base import BaseController, render
import adhocracy.forms as forms
import adhocracy.lib.text as text


log = logging.getLogger(__name__)

    
class IssueFilterForm(formencode.Schema):
    allow_extra_fields = True
    issues_q = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)

class IssueController(BaseController):

    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    @validate(schema=IssueFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        issues = model.Issue.all(c.instance if c.instance else None)
        
        if format == 'json':
            return render_json(issues)
        
        c.issues_pager = pager.issues(issues, has_query=False)
        c.tile = tiles.instance.InstanceTile(c.instance)
        return render("/issue/index.html")
    
    
    def new(self, format='html'):
        return self.not_implemented(format)
    
    
    def create(self, format='html'):
        return self.not_implemented(format)
    
    
    def edit(self, id, format='html'):
        return self.not_implemented(format)
    
    
    def update(self, id, format='html'):
        return self.not_implemented(format)
    
    
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
        return render("/issue/discussion.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def activity(self, id, format='html'):
        c.issue = get_entity_or_abort(model.Issue, id)
        events = model.Event.find_by_topics([c.issue] + c.issue.proposals)
        
        if format == 'rss':
            return event.rss_feed(events, _("Issue: %s") % c.issue.label,
                                  h.instance_url(c.instance, path="/issue/%s" % str(c.issue.id)),
                                  description=_("Activity on the %s issue") % c.issue.label)
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.events_pager = pager.events(events)
        return render("/issue/activity.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def proposals(self, id, format="html"):
        c.issue = get_entity_or_abort(model.Issue, id)
        
        if format == 'json':
            return render_json(c.issue.proposals)
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.proposals_pager = pager.proposals(c.issue.proposals, detail=True)
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
        return render("/issue/delegations.html")
    
    
    def delete(self, id, format='html'):
        return self.not_implemented(format)
    

