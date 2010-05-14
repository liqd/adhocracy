import cgi, math
from datetime import datetime

from pylons.i18n import _
from formencode import foreach, Invalid

from adhocracy.lib.base import *
import adhocracy.lib.text as libtext
import adhocracy.forms as forms
from adhocracy.lib.tiles.proposal_tiles import ProposalTile


log = logging.getLogger(__name__)


class PageCreateForm(formencode.Schema):
    allow_extra_fields = True
    title = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=20000, min=4, not_empty=True)
    function = forms.ValidPageFunction()
    parent = forms.ValidPage(if_missing=None, if_empty=None, not_empty=False)
    proposal = forms.ValidProposal(not_empty=False, if_empty=None, if_missing=None)


class PageEditForm(formencode.Schema):
    allow_extra_fields = True
    new_variant = validators.String(not_empty=False, if_missing=None, if_empty=None)
    
    
class PageUpdateForm(formencode.Schema):
    allow_extra_fields = True
    title = validators.String(max=255, min=4, not_empty=True)
    variant = forms.VariantName(not_empty=False, if_missing=model.Text.HEAD, if_empty=model.Text.HEAD)
    text = validators.String(max=20000, min=4, not_empty=True)
    parent = forms.ValidText()

    
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
        pages = model.Page.all(instance=c.instance, functions=model.Page.LISTED)
        c.pages_pager = pager.pages(pages)
        
        if format == 'json':
            return render_json(c.pages_pager)
            
        return render("/page/index.html")
    
    
    @RequireInstance
    def new(self, errors=None):
        require.page.create()
        c.title = request.params.get('title', None)
        c.proposal = request.params.get("proposal")
        c.function = request.params.get("function", model.Page.DOCUMENT)
        return render("/page/new.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=PageCreateForm(), form='new', post_only=False, on_get=True)
    def create(self, format='html'):
        require.page.create()
        
        # a proposal that this norm should be integrated with 
        proposal = self.form_result.get("proposal")
        _function = self.form_result.get("function")
        _text = self.form_result.get("text")
        
        # snub out invalid page types 
        if _function not in [model.Page.DOCUMENT, model.Page.NORM]:
            _function = model.Page.DOCUMENT
        
        if _function == model.Page.NORM:
            # if a proposal is specified, create a stub:
            if proposal is not None:
                _text = None
            
            # else, if the user cannot create norms:
            if proposal is None and not can.norm.create():
                _function = model.Page.DOCUMENT
                
        page = model.Page.create(c.instance, self.form_result.get("title"), 
                                 _text, c.user, function=_function)
        
        if self.form_result.get("parent") is not None:
            page.parents.append(self.form_result.get("parent"))
        
        target = page # by default, redirect to the page
        if proposal is not None and _function == model.Page.NORM:
            variant = libtext.title2alias(proposal.title)
            text = model.Text.create(page, variant, c.user, 
                                     self.form_result.get("title"), 
                                     self.form_result.get("text"),
                                     parent=page.head)
            # if a selection was created, go there instead:
            target = model.Selection.create(proposal, page, c.user)
        
        model.meta.Session.commit()
        watchlist.check_watch(page)
        event.emit(event.T_PAGE_CREATE, c.user, instance=c.instance, 
                   topics=[page], page=page, rev=page.head)
        
        redirect(h.entity_url(target))


    @RequireInstance
    @validate(schema=PageEditForm(), form='edit', post_only=False, on_get=True)
    def edit(self, id, variant=None, text=None):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        
        new_variant = self.form_result.get('new_variant')
        if new_variant is not None:
            variant = libtext.title2alias(new_variant)
            if variant in c.page.variants:
                for i in range(1, 100000):
                    variant = libtext.title2alias(new_variant) + str(i)
                    if not variant in c.page.variants:
                        break
            c.variant = variant
        
        require.page.variant_edit(c.page, c.variant)
        c.text_rows = libtext.field_rows(c.text.text)
        
        if c.page.has_variants and c.variant != model.Text.HEAD:
            require.norm.edit(c.page, variant)
            c.left = c.page.head
            right_html = c.text.render()
            left_html = c.left.render()
            c.right_diff = libtext.html_diff(left_html, right_html)
            return render('/page/diff_edit.html')
        return render('/page/edit.html')
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=PageUpdateForm(), form='edit', post_only=False, on_get=True)
    def update(self, id, variant=None, text=None, format='html'):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        c.variant = self.form_result.get("variant")
        require.page.variant_edit(c.page, c.variant)
        
        parent = self.form_result.get("parent")
        if parent.page != c.page:
            return ret_abort(_("You're trying to update to a text which is not part of this pages history"),
                             code=400, format=format)
        
        text = model.Text.create(c.page, 
                      c.variant, c.user, 
                      self.form_result.get("title"), 
                      self.form_result.get("text"),
                      parent=parent)
        model.meta.Session.commit()
        watchlist.check_watch(c.page)
        event.emit(event.T_PAGE_EDIT, c.user, instance=c.instance, 
                   topics=[c.page], page=c.page, rev=text)
        redirect(h.entity_url(text))
    
    
    @RequireInstance
    def show(self, id, variant=None, text=None, format='html'):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        require.page.show(c.page)
        if c.text.variant != c.variant:
            abort(404, _("The variant %s does not exist!") % c.variant)
        if c.variant != model.Text.HEAD:
            options = [c.page.variant_head(v) for v in c.page.variants]
            return self._differ(c.page.head, c.text, options=options)
        #redirect(h.entity_url(c.text))
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/show.html")
        
    
    @RequireInstance
    def history(self, id, variant=model.Text.HEAD, text=None, format='html'):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        require.page.show(c.page)
        c.texts_pager = NamedPager('texts', c.text.history, 
                                   tiles.text.history_row, count=10, #list_item,
                                   sorts={_("oldest"): sorting.entity_oldest,
                                          _("newest"): sorting.entity_newest},
                                   default_sort=sorting.entity_newest)
        if format == 'json':
            return render_json(c.texts_pager)
        c.tile = tiles.page.PageTile(c.page)
        return render('/page/history.html')
    
    
    @RequireInstance
    @validate(schema=PageDiffForm(), form='bad_request', post_only=False, on_get=True)
    def diff(self):
        left = self.form_result.get('left')
        right = self.form_result.get('right')
        options = [right.page.variant_head(v) for v in right.page.variants]
        return self._differ(left, right, options=options)
        
        
    def _differ(self, left, right, options=None):
        if left == right: 
            h.flash(_("Cannot compare identical text revisions."))
            redirect(h.entity_url(right))
        c.left, c.right = (left, right)
        c.left_options = options
        require.page.show(c.left.page)
        if c.left.page != c.right.page:
            require.page.show(c.right.page)
        right_html = right.render()
        left_html = left.render()
        #c.left_diff = text.html_diff(right_html, left_html)
        #c.left_diff = text.html_diff(right_html, left_html)
        c.right_diff = libtext.html_diff(left_html, right_html)
        c.tile = tiles.page.PageTile(c.right.page)
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
            variant = _text.variant
        elif variant is not None:
            _text = page.variant_head(variant)
            if _text is None:
                _text = page.head
        else: 
            variant = _text.variant
        return (page, _text, variant)
    
    
    def _common_metadata(self, page):
        pass
