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
    categories = formencode.Any(formencode.foreach.ForEach(forms.ValidCategory(), convert_to_list=True))

class IssueEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(max=255, min=4, not_empty=True)
    categories = formencode.Any(formencode.foreach.ForEach(forms.ValidCategory(), convert_to_list=True))

class IssueController(BaseController):

    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("issue.create"))
    @validate(schema=IssueCreateForm(), form="create", post_only=True)
    def create(self):
        auth.require_delegateable_perm(None, 'issue.create')
        if request.method == "POST":
            issue = model.Issue(c.instance, self.form_result.get('label'), c.user)
            issue.parents = self.form_result.get('categories')
            comment = model.Comment(issue, c.user)
            rev = model.Revision(comment, c.user, 
                                 text.cleanup(self.form_result.get("text")))
            comment.latest = rev
            model.meta.Session.add(issue)
            model.meta.Session.add(comment)
            model.meta.Session.add(rev)
            model.meta.Session.commit()
            issue.comment = comment
            model.meta.Session.add(issue)
            model.meta.Session.commit()
            model.meta.Session.refresh(rev)
            
            event.emit(event.T_ISSUE_CREATE, {'issue': issue}, c.user, 
                       scopes=[c.instance], topics=[issue, c.instance])
            
            redirect_to('/issue/%s' % str(issue.id))
        return render("/issue/create.html")
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("issue.edit"))
    @validate(schema=IssueEditForm(), form="edit", post_only=True)
    def edit(self, id):
        c.issue = model.Issue.find(id)
        if not c.issue: 
            abort(404, _("No issue with ID %s exists." % id))
        auth.require_delegateable_perm(c.issue, 'issue.edit')
        if request.method == "POST":
            c.issue.label = self.form_result.get('label')
            c.issue.parents = self.form_result.get('categories')
            model.meta.Session.add(c.issue)
            model.meta.Session.commit()
            model.meta.Session.refresh(c.issue)
            
            event.emit(event.T_ISSUE_EDIT, {'issue': c.issue}, c.user, 
                       scopes=[c.instance], topics=[c.issue, c.instance])
            
            redirect_to('/issue/%s' % str(c.issue.id))
        return render("/issue/edit.html")
    
    @RequireInstance
    @ActionProtector(has_permission("issue.view"))
    def view(self, id, format="html"):
        c.issue = model.Issue.find(id)
        if not c.issue: 
            abort(404, _("No issue with ID %s exists." % id))
        
        h.add_meta("dc.title", text.meta_escape(c.issue.label, markdown=False))
        h.add_meta("dc.date", c.issue.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author", text.meta_escape(c.issue.creator.name, markdown=False))
        
        if format == 'rss':
            events = event.q.run(event.q._or(event.q.topic(c.issue), "foo:schnasel",
                             *map(event.q.topic, c.issue.motions)))
        
            return event.rss_feed(events, _("Issue: %s") % c.issue.label,
                                  h.instance_url(c.instance, path="/issue/%s" % str(c.issue.id)),
                                  description=_("Activity on the %s issue") % c.issue.label)
        
        h.add_rss(_("Issue: %(issue)s") % {'issue': c.issue.label}, 
            h.instance_url(c.instance, "/issue/%s.rss" % c.issue.id))
        
        c.tile = tiles.issue.IssueTile(c.issue)
        c.motions_pager = NamedPager('motions', c.tile.motions, tiles.motion.row, count=4, #list_item,
                                     sorts={_("oldest"): sorting.entity_oldest,
                                            _("newest"): sorting.entity_newest,
                                            _("activity"): sorting.motion_activity,
                                            _("name"): sorting.delegateable_label},
                                     default_sort=sorting.motion_activity)
        
        #c.events_pager = NamedPager('events', events, tiles.event.list_item, count=5)
        
        return render("/issue/view.html")
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("issue.delete"))
    def delete(self, id):
        c.issue = model.Issue.find(id)
        if not c.issue: 
            abort(404, _("No issue with ID %s exists." % id))
        auth.require_delegateable_perm(c.issue, 'issue.delete')
        parent = c.issue.parents[0]
        
        for motion in c.issue.motions:
            state = democracy.State(motion)
            if not state.motion_mutable:
                h.flash(_("The issue %(issue)s cannot be deleted, because the contained " +
                          "motion %(motion)s is polling.") % {'issue': c.issue.label, 'motion': motion.label})
                redirect_to('/issue/%s' % str(c.issue.id))
            motion.delete_time = datetime.now()
            model.meta.Session.add(motion)
        
        h.flash(_("Issue '%(issue)s' has been deleted.") % {'issue': c.issue.label})
        
        c.issue.delete_time = datetime.now()
        model.meta.Session.add(c.issue)
        model.meta.Session.commit()
        
        event.emit(event.T_ISSUE_DELETE, {'issue': c.issue},
                   c.user, scopes=[c.instance], topics=[c.issue, c.instance] + c.issue.parents)
        
        redirect_to('/category/%s' % str(parent.id)) 
    
    
