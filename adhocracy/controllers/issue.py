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

class IssueController(BaseController):

    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("issue.create"))
    @validate(schema=IssueCreateForm(), form="create", post_only=True)
    def create(self):
        if request.method == "POST":
            issue = model.Issue(c.instance, self.form_result.get('label'), c.user)
            model.meta.Session.add(issue)
            comment = model.Comment.create(self.form_result.get('text'), 
                                           c.user, issue)
            model.meta.Session.commit()
            issue.comment = comment
            model.meta.Session.commit()
            
            watchlist.check_watch(issue)
            
            event.emit(event.T_ISSUE_CREATE, c.user, instane=c.instance, 
                       topics=[issue], issue=issue)
            
            redirect_to('/issue/%s' % str(issue.id))
        return render("/issue/create.html")
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("issue.edit"))
    @validate(schema=IssueEditForm(), form="edit", post_only=True)
    def edit(self, id):
        c.issue = get_entity_or_abort(model.Issue, id)
        if request.method == "POST":
            c.issue.label = self.form_result.get('label')
            model.meta.Session.add(c.issue)
            model.meta.Session.commit()
            model.meta.Session.refresh(c.issue)
            
            watchlist.check_watch(c.issue)
            
            event.emit(event.T_ISSUE_EDIT, c.user, instance=c.instance, 
                       topics=[c.issue], issue=c.issue)
            
            redirect_to('/issue/%s' % str(c.issue.id))
        return render("/issue/edit.html")
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def view(self, id, format="html"):
        c.issue = get_entity_or_abort(model.Issue, id)
        h.add_meta("dc.title", text.meta_escape(c.issue.label, markdown=False))
        h.add_meta("dc.date", c.issue.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", text.meta_escape(c.issue.creator.name, markdown=False))
        
        if format == 'rss':
            query = model.meta.Session.query(model.Event)
            query = query.join(model.Event.topics)
            ids = map(lambda d: d.id, [c.issue]+c.issue.proposals)
            query = query.filter(model.Event.topics.any(model.Issue.id.in_(ids)))
            query = query.order_by(model.Event.time.desc())
            query = query.limit(50)        
            return event.rss_feed(query.all(), _("Issue: %s") % c.issue.label,
                                  h.instance_url(c.instance, path="/issue/%s" % str(c.issue.id)),
                                  description=_("Activity on the %s issue") % c.issue.label)
        
        h.add_rss(_("Issue: %(issue)s") % {'issue': c.issue.label}, 
            h.instance_url(c.instance, "/issue/%s.rss" % c.issue.id))
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.proposals_pager = NamedPager('proposals', c.issue.proposals, tiles.proposal.row, #list_item,
                                     sorts={_("oldest"): sorting.entity_oldest,
                                            _("newest"): sorting.entity_newest,
                                            _("activity"): sorting.proposal_activity,
                                            _("newest comment"): sorting.delegateable_latest_comment,
                                            _("name"): sorting.delegateable_label},
                                     default_sort=sorting.proposal_activity)
        return render("/issue/view.html")
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def activity(self, id, format='html'):
        c.issue = get_entity_or_abort(model.Issue, id)
        events = model.Event.find_by_topics([c.issue] + c.issue.proposals)
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.events_pager = NamedPager('events', events, tiles.event.row, count=10)
        return render("/issue/activity.html")
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def proposals(self, id, format="html"):
        c.issue = get_entity_or_abort(model.Issue, id)
        c.tile = tiles.issue.IssueTile(c.issue)
        c.proposals_pager = NamedPager('proposals', c.issue.proposals, tiles.proposal.row,  #list_item,
                             sorts={_("oldest"): sorting.entity_oldest,
                                    _("newest"): sorting.entity_newest,
                                    _("activity"): sorting.proposal_activity,
                                    _("newest comment"): sorting.delegateable_latest_comment,
                                    _("name"): sorting.delegateable_label},
                             default_sort=sorting.proposal_activity)
        return render("/issue/proposals.html")
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def delegations(self, id, format="html"):
        c.issue = get_entity_or_abort(model.Issue, id)
        
        delegations = c.issue.current_delegations()
        if format == 'json':
            return render_json(list(delegations))
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.delegations_pager = NamedPager('delegations', delegations, tiles.delegation.row,  #list_item,
                             sorts={_("oldest"): sorting.entity_oldest,
                                    _("newest"): sorting.entity_newest},
                             default_sort=sorting.entity_newest)
        return render("/issue/delegations.html")
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("issue.delete"))
    def delete(self, id):
        c.issue = get_entity_or_abort(model.Issue, id)        
        for proposal in c.issue.proposals:
            if not democracy.is_proposal_mutable(proposal):
                h.flash(_("The issue %(issue)s cannot be deleted, because the contained " +
                          "proposal %(proposal)s is polling.") % {'issue': c.issue.label, 'proposal': proposal.label})
                redirect_to('/issue/%s' % str(c.issue.id))
        
        h.flash(_("Issue '%(issue)s' has been deleted.") % {'issue': c.issue.label})
        
        c.issue.delete()
        model.meta.Session.commit()
        
        event.emit(event.T_ISSUE_DELETE, c.user, instance=c.instance, 
                   topics=[c.issue], issue=c.issue)
        
        redirect_to('/instance/%s' % str(c.instance.key)) 
    
    
