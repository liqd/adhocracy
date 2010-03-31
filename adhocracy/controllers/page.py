import cgi
from datetime import datetime

from pylons.i18n import _
from formencode import foreach, Invalid

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.forms as forms
from adhocracy.lib.tiles.proposal_tiles import ProposalTile


log = logging.getLogger(__name__)


class PageCreateForm(formencode.Schema):
    allow_extra_fields = True
    title = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=20000, min=4, not_empty=True)

    
class PageUpdateForm(formencode.Schema):
    allow_extra_fields = True
    title = validators.String(max=255, min=4, not_empty=True)
    variant = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=20000, min=4, not_empty=True)

    
class PageFilterForm(formencode.Schema):
    allow_extra_fields = True
    pages_q = validators.String(max=255, not_empty=False, if_empty=u'', if_missing=u'')


class PageController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("page.view"))
    @validate(schema=PageFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        pages = model.Page.all(instance=c.instance)
        c.pages_pager = pager.pages(pages)
        
        if format == 'json':
            return render_json(c.pages_pager)
            
        return render("/page/index.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("page.create"))
    def new(self, errors=None):
        c.title = request.params.get('title', None)
        return render("/page/new.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("page.create"))
    @validate(schema=PageCreateForm(), form='new', post_only=False, on_get=True)
    def create(self, format='html'):
        page = model.Page.create(c.instance, self.form_result.get("title"), 
                                 self.form_result.get("text"), c.user)
        model.meta.Session.commit()
        redirect(h.entity_url(page))


    @RequireInstance
    @ActionProtector(has_permission("page.edit")) 
    def edit(self, id, variant=None, text=None):
        c.page, c.text = self._get_page_and_text(id, variant, text)
        return render('/page/edit.html')
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("page.edit")) 
    @validate(schema=PageUpdateForm(), form='edit', post_only=False, on_get=True)
    def update(self, id, variant=None, text=None, format='html'):
        c.page, c.text = self._get_page_and_text(id, variant, text)
        text = model.Text.create(c.page, 
                      self.form_result.get("variant"),  
                      c.user, 
                      self.form_result.get("title"), 
                      self.form_result.get("text"),
                      parent=c.page.head)
        model.meta.Session.commit()
        redirect(h.entity_url(c.page))
    
    
    @RequireInstance
    @ActionProtector(has_permission("page.view"))
    def show(self, id, variant=None, text=None, format='html'):
        c.page, c.text = self._get_page_and_text(id, variant, text)
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/show.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("page.delete"))
    def ask_delete(self, id):
        c.page = get_entity_or_abort(model.Page, id)
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/ask_delete.html")
    
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("page.delete"))
    def delete(self, id):
        c.page = get_entity_or_abort(model.Page, id) 
        c.page.delete()
        model.meta.Session.commit()
        h.flash(_("The page %s has been deleted.") % c.page.title)
        redirect(h.entity_url(c.page.instance))
    
    
    def _get_page_and_text(self, id, variant, text):
        page = get_entity_or_abort(model.Page, id)
        _text = page.head
        if text is not None:
            _text = get_entity_or_abort(model.Text, text)
            if _text.page != page or (variant and _text.variant != variant):
                abort(404, _("Invalid text ID %s for this page/variant!"))
        elif variant is not None:
            _text = page.variant_head(variant)
            if _text is None:
                abort(404, _("There is no variant %s of %s") % (variant, page.title))
        return (page, _text)
    
    
    def _common_metadata(self, page):
        pass
