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
    variant = validators.String(max=255, min=1, not_empty=False, 
                if_empty=model.Text.HEAD, if_missing=model.Text.HEAD)
    text = validators.String(max=20000, min=4, not_empty=True)

    
class PageFilterForm(formencode.Schema):
    allow_extra_fields = True
    pages_q = validators.String(max=255, not_empty=False, if_empty=u'', if_missing=u'')

    
class PageDiffForm(formencode.Schema):
    allow_extra_fields = True
    left = forms.ValidText()
    right = forms.ValidText()


class PageController(BaseController):
    
    @RequireInstance
    @validate(schema=PageFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        require.page.index()
        pages = model.Page.all(instance=c.instance)
        c.pages_pager = pager.pages(pages)
        
        if format == 'json':
            return render_json(c.pages_pager)
            
        return render("/page/index.html")
    
    
    @RequireInstance
    def new(self, errors=None):
        require.page.create()
        c.title = request.params.get('title', None)
        return render("/page/new.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=PageCreateForm(), form='new', post_only=False, on_get=True)
    def create(self, format='html'):
        require.page.create()
        page = model.Page.create(c.instance, self.form_result.get("title"), 
                                 self.form_result.get("text"), c.user)
        model.meta.Session.commit()
        watchlist.check_watch(page)
        event.emit(event.T_PAGE_CREATE, c.user, instance=c.instance, 
                   topics=[page], page=page, text=page.head)
        redirect(h.entity_url(page))


    @RequireInstance
    def edit(self, id, variant=None, text=None):
        c.page, c.text = self._get_page_and_text(id, variant, text)
        require.page.edit(c.page)
        return render('/page/edit.html')
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=PageUpdateForm(), form='edit', post_only=False, on_get=True)
    def update(self, id, variant=None, text=None, format='html'):
        c.page, c.text = self._get_page_and_text(id, variant, text)
        require.page.edit(c.page)
        text = model.Text.create(c.page, 
                      self.form_result.get("variant"),  
                      c.user, 
                      self.form_result.get("title"), 
                      self.form_result.get("text"),
                      parent=c.page.head)
        model.meta.Session.commit()
        watchlist.check_watch(c.page)
        event.emit(event.T_PAGE_EDIT, c.user, instance=c.instance, 
                   topics=[c.page], page=c.page, text=text)
        redirect(h.entity_url(text))
    
    
    @RequireInstance
    def show(self, id, variant=None, text=None, format='html'):
        c.page, c.text = self._get_page_and_text(id, variant, text)
        require.page.show(c.page)
        #redirect(h.entity_url(c.text))
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/show.html")
    
    
    @RequireInstance
    @validate(schema=PageDiffForm(), form='bad_request', post_only=False, on_get=True)
    def diff(self):
        c.left = self.form_result.get('left')
        require.page.show(c.left.page)
        left_html = c.left.render()
        c.right = self.form_result.get('right')
        require.page.show(c.right.page)
        right_html = c.right.render()
        
        c.left_diff = text.html_diff(right_html, left_html)
        c.right_diff = text.html_diff(left_html, right_html)
        return render("/page/diff.html")
        
    
    @RequireInstance
    def ask_delete(self, id):
        c.page = get_entity_or_abort(model.Page, id)
        require.page.delete(c.page)
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/ask_delete.html")
    
    
    @RequireInstance
    @RequireInternalRequest()
    def delete(self, id):
        c.page = get_entity_or_abort(model.Page, id) 
        require.page.delete(c.page)
        c.page.delete()
        model.meta.Session.commit()
        event.emit(event.T_PAGE_DELETE, c.user, instance=c.instance, 
                   topics=[c.page], page=c.page)
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
