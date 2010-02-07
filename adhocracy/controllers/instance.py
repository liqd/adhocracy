from datetime import datetime
import hashlib
import os.path
from time import time
import rfc822

from pylons.controllers.util import etag_cache
from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms
import adhocracy.lib.logo as logo

import adhocracy.lib.instance as libinstance

log = logging.getLogger(__name__)

class InstanceCreateForm(formencode.Schema):
    allow_extra_fields = True
    key = formencode.All(validators.String(min=4, max=20),
                              forms.UniqueInstanceKey())
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    
class InstanceEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    activation_delay = validators.Int(not_empty=True)
    required_majority = validators.Number(not_empty=True)
    default_group = forms.ValidGroup(not_empty=True)

class InstanceFilterForm(formencode.Schema):
    allow_extra_fields = True
    issues_q = validators.String(max=255, not_empty=False, if_empty=None, if_missing=None)

class InstanceController(BaseController):
    
    @ActionProtector(has_permission("instance.index"))
    def index(self):
        h.add_meta("description", _("An index of adhocracies run at adhocracy.cc. " + 
                                    "Select which ones you would like to join and participate in!"))
        
        instances = model.Instance.all()
        c.instances_pager = NamedPager('instances', instances, tiles.instance.row,
                                       sorts={_("oldest"): sorting.entity_oldest,
                                              _("newest"): sorting.entity_newest,
                                              _("activity"): sorting.instance_activity,
                                              _("name"): sorting.delegateable_label},
                                       default_sort=sorting.instance_activity)
        return render("/instance/index.html")  
    
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("instance.create"))
    @validate(schema=InstanceCreateForm(), form="create", post_only=True)
    def create(self):
        if request.method == "POST":
            inst = libinstance.create(self.form_result.get('key'),
                                      self.form_result.get('label'),
                                      c.user)
            inst.description = text.cleanup(self.form_result.get('description'))
            model.meta.Session.add(inst)
            model.meta.Session.commit()
            model.meta.Session.refresh(inst)
            
            event.emit(event.T_INSTANCE_CREATE, c.user, instance=inst)
            
            redirect_to(h.instance_url(inst))
        return render("/instance/create.html")

    @RequireInstance
    @ActionProtector(has_permission("instance.view"))
    @validate(schema=InstanceFilterForm(), post_only=False, on_get=True)
    def view(self, key, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        
        query = self.form_result.get('issues_q')
        issues = []
        if query:
            issues = libsearch.query.run(query + "*", instance=c.page_instance, 
                                         entity_type=model.Issue)
        else:
            issues = model.Issue.all(instance=c.page_instance)
        
        if format == 'rss':
            query = model.meta.Session.query(model.Event)
            query = query.filter(model.Event.instance==c.page_instance)
            query = query.order_by(model.Event.time.desc())
            query = query.limit(25)
            return event.rss_feed(query.all(), _('%s News' % c.page_instance.label),
                                      h.instance_url(c.page_instance), 
                                      _("News from %s") % c.page_instance.label)
        
        #c.events_pager = NamedPager('events', events, tiles.event.list_item, count=20)
        
        c.tile = tiles.instance.InstanceTile(c.page_instance)
        
        sorts = {_("oldest"): sorting.entity_oldest,
                 _("newest"): sorting.entity_newest,
                 _("activity"): sorting.issue_activity,
                 _("newest comment"): sorting.delegateable_latest_comment,
                 _("name"): sorting.delegateable_label}
        if query:
            sorts[_("relevance")] = sorting.entity_stable
        
        c.issues_pager = NamedPager('issues', issues, tiles.issue.row, sorts=sorts,
                                    default_sort=sorting.entity_stable if query else sorting.issue_activity)

        return render("/instance/view.html")
    
    @RequireInstance
    @ActionProtector(has_permission("instance.view"))
    def activity(self, key):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        
        query = model.meta.Session.query(model.Event)
        query = query.filter(model.Event.instance==c.page_instance)
        query = query.order_by(model.Event.time.desc())
        query = query.limit(100)
        
        c.tile = tiles.instance.InstanceTile(c.page_instance)
        c.events_pager = NamedPager('events', query.all(), tiles.event.row, count=10)
        return render("/instance/activity.html")
            
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("instance.admin"))
    @validate(schema=InstanceEditForm(), form="edit", post_only=True)
    def edit(self, key):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        if request.method == "POST":
            c.page_instance.description = text.cleanup(self.form_result.get('description'))
            c.page_instance.label = self.form_result.get('label')
            c.page_instance.required_majority = self.form_result.get('required_majority')
            c.page_instance.activation_delay = self.form_result.get('activation_delay')
            if self.form_result.get('default_group').code in model.Group.INSTANCE_GROUPS:
                c.page_instance.default_group = self.form_result.get('default_group') 
            
            try:
                if 'logo' in request.POST and hasattr(request.POST.get('logo'), 'file') and \
                    request.POST.get('logo').file:
                    logo.store(c.page_instance, request.POST.get('logo').file)
            except Exception, e:
                h.flash(unicode(e))
                log.debug(e)
            
            model.meta.Session.add(c.page_instance)
            model.meta.Session.commit()
                        
            event.emit(event.T_INSTANCE_EDIT, c.user, instance=c.page_instance)
            
            #h.flash("%s has been updated." % c.page_instance.label)
            redirect_to(h.instance_url(c.page_instance))
        c._Group = model.Group
        return htmlfill.render(render("/instance/edit.html"),
                               defaults={
                                    'label': c.page_instance.label,
                                    'description': c.page_instance.description,
                                    'required_majority': c.page_instance.required_majority,
                                    'activation_delay': c.page_instance.activation_delay,
                                    'default_group': c.page_instance.default_group.code if \
                                                     c.page_instance.default_group else \
                                                     model.Group.INSTANCE_DEFAULT
                                         })
    
    def _set_image_headers(self, path, io):
        mtime = os.path.getmtime(path)
        response.content_type = "image/png"
        etag_cache(key=str(mtime))
        response.charset = None
        response.last_modified = rfc822.formatdate(timeval=mtime)
        del response.headers['Cache-Control']
        response.content_length = len(io)
        response.pragma = None 
    
    @ActionProtector(has_permission("instance.index"))
    def header(self, key):
        c.page_instance = model.Instance.find(key)
        (path, io) = logo.load_header(c.page_instance)
        self._set_image_headers(path, io) 
        return io
        
    @ActionProtector(has_permission("instance.index"))
    def icon(self, key, x, y):
        c.page_instance = model.Instance.find(key)
        try:
            (x, y) = (int(x), int(y))
        except ValueError, ve:
            log.debug(ve)
            (x, y) = (24, 24)
        (path, io) = logo.load(c.page_instance, size=(x, y))
        self._set_image_headers(path, io)
        return io            
    
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.delete"))
    def delete(self, key):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        abort(500, _("Deleting an instance is not currently implemented"))
    
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.join"))
    def join(self, key):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        if c.page_instance in c.user.instances:
            h.flash(_("You're already a member in %(instance)s.") % {
                            'instance': c.page_instance.label})
            redirect_to('/adhocracies')
        membership = model.Membership(c.user, c.page_instance, 
                                      c.page_instance.default_group)
        model.meta.Session.expunge(membership)
        model.meta.Session.add(membership)
        model.meta.Session.commit()
        
        event.emit(event.T_INSTANCE_JOIN, c.user, instance=c.page_instance)
        
        h.flash(_("Welcome to %(instance)s") % {
                        'instance': c.page_instance.label})
        return redirect_to(h.instance_url(c.page_instance))
        
    @RequireInternalRequest()            
    @ActionProtector(has_permission("instance.leave"))
    def leave(self, key):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        if not c.page_instance in c.user.instances:
            h.flash(_("You're not a member of %(instance)s.") % {
                            'instance': c.page_instance.label})
        elif c.user == c.page_instance.creator:
            h.flash(_("You're the founder of %s, cannot leave.") % {
                            'instance': c.page_instance.label})
        else:
            t = datetime.utcnow()
            
            for membership in c.user.memberships:
                if membership.expire_time:
                    continue
                if membership.instance == c.page_instance:
                    membership.expire_time = t
                    model.meta.Session.add(membership)
                    
                    democracy.DelegationNode.detach(c.user, c.page_instance)
                    
                    event.emit(event.T_INSTANCE_LEAVE,  c.user, instance=c.page_instance)
            model.meta.Session.commit()
        redirect_to('/adhocracies')
        
    @ActionProtector(has_permission("issue.view"))
    @validate(schema=InstanceFilterForm(), post_only=False, on_get=True)
    def filter(self, key):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        query = self.form_result.get('issues_q', '')
        issues = libsearch.query.run(query + "*", instance=c.page_instance, 
                                     entity_type=model.Issue)
        c.issues_pager = NamedPager('issues', issues, tiles.issue.row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest,
                                           _("activity"): sorting.issue_activity,
                                           _("relevance"): sorting.entity_stable,
                                           _("name"): sorting.delegateable_label},
                                    default_sort=sorting.entity_stable)
        return c.issues_pager.here()

