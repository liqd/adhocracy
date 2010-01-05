from datetime import datetime

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

    @ActionProtector(has_permission("instance.view"))
    def view(self, key, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, key)
        
        issues = model.Issue.all(instance=c.page_instance)
        
        if format == 'rss':
            query = model.meta.Session.query(model.Event)
            query = query.filter(model.Event.instance==c.page_instance)
            query = query.order_by(model.Event.time.desc())
            query = query.limit(50)
            return event.rss_feed(query.all(), _('%s News' % c.page_instance.label),
                                      h.instance_url(c.page_instance), 
                                      _("News from the %s Adhocracy") % c.page_instance.label)
        
        #c.events_pager = NamedPager('events', events, tiles.event.list_item, count=20)
        
        c.tile = tiles.instance.InstanceTile(c.page_instance)
        
        c.issues_pager = NamedPager('issues', issues, tiles.issue.row, 
                                    sorts={_("oldest"): sorting.entity_oldest,
                                           _("newest"): sorting.entity_newest,
                                           _("activity"): sorting.issue_activity,
                                           _("name"): sorting.delegateable_label},
                                    default_sort=sorting.issue_activity)

        return render("/instance/view.html")
            
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
                if request.POST.get('logo').file:
                    logo.store(c.page_instance, request.POST.get('logo').file)
            except Exception, e:
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
    
    @ActionProtector(has_permission("instance.index"))
    def header(self, key):
        c.page_instance = model.Instance.find(key)
        etag_cache(str(c.page_instance.id if c.page_instance else 0))
        response.headers['Content-type'] = 'image/png'
        #response.content_type = "image/png"
        return logo.load(c.page_instance, header=True)
        
    @ActionProtector(has_permission("instance.index"))
    def icon(self, key, x, y):
        c.page_instance = model.Instance.find(key)
        etag_cache(str(c.page_instance.id if c.page_instance else 0))
        response.headers['Content-type'] = 'image/png'
        try:
            (x, y) = (int(x), int(y))
        except ValueError, ve:
            log.debug(ve)
            (x, y) = (24, 24)
        return logo.load(c.page_instance, size=(x, y), header=False)            
    
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
        
        grp = c.page_instance.default_group
        if not grp:
            grp = model.Group.by_code(model.Group.INSTANCE_DEFAULT) 
        membership = model.Membership(c.user, c.page_instance, grp)
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
            t = datetime.now()
            
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


