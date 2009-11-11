from datetime import datetime
import os.path
import StringIO

from pylons.i18n import _

import Image

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms

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
    
    def __init__(self):
        self.LOGO = Image.open(os.path.join(config['pylons.paths']['static_files'], 
                                            'img', 'header_logo.png'))
        self.PATH = os.path.join(config['cache.dir'], 'img', '%(key)s.png')    
    
    def _find_key(self, key):
        c.page_instance = model.Instance.find(key)
        if not c.page_instance:
            abort(404, _("No such adhocracy exists: %(key)s") % {'key': key})

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
        
        @memoize('instance-index')
        def cached(user, p):
            return render("/instance/index.html")  
        return cached(c.user, request.params)
    
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("instance.create"))
    @validate(schema=InstanceCreateForm(), form="create", post_only=True)
    def create(self):
        if request.method == "POST":
            inst = libinstance.create(self.form_result.get('key'),
                                      self.form_result.get('label'),
                                      c.user)
            inst.description = self.form_result.get('description')
            model.meta.Session.refresh(inst)
            
            event.emit(event.T_INSTANCE_CREATE, {'instance': inst.key},
                       c.user, scopes=[inst], topics=[inst])
            
            redirect_to(h.instance_url(inst))
        return render("/instance/create.html")

    @ActionProtector(has_permission("instance.view"))
    def view(self, key, format='html'):
        self._find_key(key)
        
        issues = c.page_instance.root.search_children(recurse=True, cls=model.Issue)
        
        if format == 'rss':
            query = event.q._or(event.q.scope(c.page_instance), event.q.topic(c.page_instance))
            events = event.q.run(query)
            return event.rss_feed(events, _('%s News' % c.page_instance.label),
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
        
        c.subcats_pager = NamedPager('categories', c.tile.categories, tiles.category.list_item,
                             sorts={_("oldest"): sorting.entity_oldest,
                                    _("newest"): sorting.entity_newest,
                                    _("activity"): sorting.category_activity,
                                    _("name"): sorting.delegateable_label},
                             default_sort=sorting.category_activity)

        return render("/instance/view.html")
            
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("instance.admin"))
    @validate(schema=InstanceEditForm(), form="edit", post_only=True)
    def edit(self, key):
        self._find_key(key)
        if request.method == "POST":
            c.page_instance.description = text.cleanup(self.form_result.get('description'))
            c.page_instance.label = self.form_result.get('label')
            c.page_instance.required_majority = self.form_result.get('required_majority')
            c.page_instance.activation_delay = self.form_result.get('activation_delay')
            if self.form_result.get('default_group').code in model.Group.INSTANCE_GROUPS:
                c.page_instance.default_group = self.form_result.get('default_group') 
            
            try:
                logo = request.POST.get('logo')
                if logo.file:
                    logo_image = Image.open(logo.file)
                    logo_image.thumbnail(self.LOGO.size, Image.ANTIALIAS)
                    logo_image.save(self.PATH % {'key': c.page_instance.key})
            except Exception, e:
                log.debug(e)
            
            model.meta.Session.add(c.page_instance)
            model.meta.Session.commit()
                        
            event.emit(event.T_INSTANCE_EDIT, {'instance': c.page_instance},
                       c.user, scopes=[c.page_instance], topics=[c.page_instance])
            
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
    def logo(self, key):
        #self._logo_setup()
        instance = model.Instance.find(key)
        response.content_type = "application/png"
        if instance:
            instance_path = self.PATH % {'key': instance.key}
            if os.path.exists(instance_path):
                return open(instance_path, 'rb').read()
        sio = StringIO.StringIO()
        self.LOGO.save(sio, 'PNG')
        return sio.getvalue()
             
    
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.delete"))
    def delete(self, key):
        self._find_key(key)
        abort(500, _("Deleting an instance is not currently implemented"))
    
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.join"))
    def join(self, key):
        self._find_key(key)
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
        
        event.emit(event.T_INSTANCE_JOIN, {'instance': c.page_instance},
                   c.user, scopes=[c.page_instance], topics=[c.page_instance])
        
        h.flash(_("Welcome to %(instance)s") % {
                        'instance': c.page_instance.label})
        return redirect_to(h.instance_url(c.page_instance))
        
    @RequireInternalRequest()            
    @ActionProtector(has_permission("instance.leave"))
    def leave(self, key):
        self._find_key(key)
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
                    
                    event.emit(event.T_INSTANCE_LEAVE, 
                               {'instance': c.page_instance.key},
                               c.user, scopes=[c.page_instance], 
                               topics=[c.page_instance])
            model.meta.Session.commit()
        redirect_to('/adhocracies')


