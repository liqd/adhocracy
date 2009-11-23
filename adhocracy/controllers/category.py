from datetime import datetime

from pylons.i18n import _

import adhocracy.lib.text as text
from adhocracy.lib.base import *
from adhocracy.model.forms import CategoryCreateForm, CategoryEditForm

log = logging.getLogger(__name__)

class CategoryController(BaseController):

    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("category.create"))
    @validate(schema=CategoryCreateForm(), form="create", post_only=True)
    def create(self):
        auth.require_delegateable_perm(None, 'category.create')
        if request.method == "POST":
            category = model.Category(c.instance, 
                                      self.form_result.get("label"), 
                                      c.user)
            category.parents.append(self.form_result.get("categories"))
            if self.form_result.get("description"):
                category.description = text.cleanup(self.form_result.get("description"))
            model.meta.Session.add(category)
            model.meta.Session.commit()
            model.meta.Session.refresh(category)
            
            watchlist.check_watch(category)
            
            event.emit(event.T_CATEGORY_CREATE, c.user, scopes=[c.instance], 
                       topics=[category, c.instance], category=category, 
                       parent=self.form_result.get("categories"))
            
            redirect_to("/category/%s" % str(category.id))
        return render("/category/create.html")
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("category.edit"))
    @validate(schema=CategoryEditForm(), form="edit", post_only=True)
    def edit(self, id):
        c.category = model.Category.find(id)
        if not c.category:
            abort(404, _("No category with ID '%s' exists.") % id)
        auth.require_delegateable_perm(c.category, 'category.edit')
        if request.method == "POST":
            c.category.label = self.form_result.get("label")
            if self.form_result.get("description"):
                c.category.description = text.cleanup(self.form_result.get("description"))
            if not c.category.id == c.instance.root:
                parent = self.form_result.get("categories")
                if not c.category.is_super(parent):
                    c.category.parents = [parent]
            model.meta.Session.add(c.category)
            model.meta.Session.commit()
            
            watchlist.check_watch(c.category)
            
            event.emit(event.T_CATEGORY_EDIT, c.user, scopes=[c.instance], 
                       topics = [c.category], category=c.category)
            
            return redirect_to('/category/%s' % str(c.category.id))
        return render("/category/edit.html")
    
    @RequireInstance
    @ActionProtector(has_permission("category.view"))
    def view(self, id, format='html'):
        c.category = model.Category.find(id)        
        if not c.category:
            abort(404, _("No category with ID '%s' exists.") % id)
        
        if c.category.instance.root == c.category:
            redirect_to("/instance/%s" % str(c.category.instance.key))
        
        if c.category.description:
            h.add_meta("description", 
                       h.text.truncate(text.meta_escape(c.category.description), 
                                       length=200, whole_word=True))
        h.add_meta("dc.title", text.meta_escape(c.category.label, markdown=False))
        h.add_meta("dc.date", c.category.create_time.strftime("%Y-%m-%d"))        
        
        c.tile = tiles.category.CategoryTile(c.category)
        if c.tile.is_root:
            c.instance_tile = tiles.instance.InstanceTile(c.instance) 
        
        issues = c.category.search_children(recurse=True, cls=model.Issue)
        
        if format == 'rss':
            events = event.q.run(event.q._or(map(event.q.topic, issues)))
            return event.rss_feed(events, _("Category: %s") % c.category.label,
                                  h.instance_url(c.instance, path="/category/%s" % c.category.id),
                                  c.category.description if c.category.description else "")
         
        h.add_rss(_("Category: %s") % c.category.label, 
                  h.instance_url(c.instance, "/category/%s.rss" % c.category.id))
        
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
        
        return render("category/view.html")
        
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("category.delete"))
    def delete(self, id):
        if id == c.instance.root.id:
            abort(500, _("Deleting the root category isn't possible."))
        category = model.Category.find(id)
        if not category:
            abort(404, _("No category with ID '%(id)s' exists.") % {'id': id})
        auth.require_delegateable_perm(category, 'category.delete')
        
        parent = c.instance.root
        if len(category.parents):
            parent = category.parents[0]
        for child in category.children:
            if category in child.parents:
                child.parents.remove(category)
            if not parent in child.parents:
                child.parents.append(parent)
            model.meta.Session.add(child)
        category.delete_time = datetime.now()
            
        h.flash(_("Category '%(category)s' has been deleted.") % {'category': category.label})
        
        model.meta.Session.add(category)
        model.meta.Session.commit()
        
        event.emit(event.T_CATEGORY_DELETE, c.user, scopes=[c.instance], 
                   topics=[parent, c.instance, category], category=category)
        
        redirect_to("/category/%s" % str(parent.id))
