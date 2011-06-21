import logging

import formencode
from formencode import htmlfill, Invalid, validators

from pylons import request, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import forms, model
from adhocracy.lib import democracy, event, helpers as h
from adhocracy.lib import pager, sorting, tiles, watchlist
from adhocracy.lib.auth import can, require
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render, render_json, ret_abort
import adhocracy.lib.text as libtext
from adhocracy.lib.util import get_entity_or_abort


log = logging.getLogger(__name__)


class NoneObject(object):
    pass

NoPage = NoneObject()


class PageCreateForm(formencode.Schema):
    allow_extra_fields = True
    title = forms.UnusedTitle()
    text = validators.String(max=20000, min=0, not_empty=False,
                             if_empty=None, if_missing=None)
    parent = forms.ValidPage(if_missing=None, if_empty=None, not_empty=False)
    proposal = forms.ValidProposal(not_empty=False, if_empty=None,
                                   if_missing=None)
    tags = validators.String(max=20000, not_empty=False)
    milestone = forms.MaybeMilestone(if_empty=None, 
            if_missing=None)


class PageEditForm(formencode.Schema):
    allow_extra_fields = True


class PageUpdateForm(formencode.Schema):
    allow_extra_fields = True
    title = forms.UnusedTitle()
    variant = forms.VariantName(not_empty=True)
    text = validators.String(max=20000, min=0, not_empty=False,
                             if_empty=None, if_missing=None)
    parent_text = forms.ValidText(if_missing=None, if_empty=None,
                                  not_empty=False)
    parent_page = forms.ValidPage(if_missing=NoPage, if_empty=None,
                                  not_empty=False)
    proposal = forms.ValidProposal(not_empty=False, if_empty=None,
                                   if_missing=None)
    milestone = forms.MaybeMilestone(if_empty=None, 
            if_missing=None)


class PageFilterForm(formencode.Schema):
    allow_extra_fields = True
    pages_q = validators.String(max=255, not_empty=False, if_empty=u'',
                                if_missing=u'')


class PageDiffForm(formencode.Schema):
    allow_extra_fields = True
    left = forms.ValidText()
    right = forms.ValidText()


class PageController(BaseController):

    @RequireInstance
    @validate(schema=PageFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        require.page.index()
        pages = model.Page.all(instance=c.instance,
                               functions=model.Page.LISTED)
        c.pages_pager = pager.pages(pages)

        if format == 'json':
            return render_json(c.pages_pager)

        tags = model.Tag.popular_tags(limit=30)
        c.cloud_tags = sorted(libtext.tag_cloud_normalize(tags),
                              key=lambda (k, c, v): k.name)
        return render("/page/index.html")

    @RequireInstance
    def new(self, errors=None):
        require.page.create()
        defaults = dict(request.params)
        defaults['watch'] = defaults.get('watch', True)
        c.title = request.params.get('title', None)
        c.proposal = request.params.get("proposal")

        html = None
        if c.proposal is not None:
            c.proposal = model.Proposal.find(c.proposal)
            html = render('/selection/propose.html')
        else:
            html = render("/page/new.html")

        return htmlfill.render(html, defaults=defaults, errors=errors,
                               force_defaults=False)

    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    def create(self, format='html'):
        require.page.create()
        try:
            self.form_result = PageCreateForm().to_python(request.params)
            # a proposal that this norm should be integrated with
            proposal = self.form_result.get("proposal")
            _text = self.form_result.get("text")
            if not can.norm.create():
                if not proposal:
                    msg = _("No proposal has been specified")
                    raise Invalid(msg, branch, state_(),
                                  error_dict={'title': msg})
                if not c.instance.allow_propose:
                    msg = _("You cannot create a new norm")
                    raise Invalid(msg, branch, state_(),
                                  error_dict={'title': msg})
                # if a proposal is specified, create a stub:
                _text = None
        except Invalid, i:
            return self.new(errors=i.unpack_errors())

        page = model.Page.create(c.instance, self.form_result.get("title"),
                                 _text, c.user,
                                 tags=self.form_result.get("tags"))

        page.milestone = self.form_result.get('milestone')

        if self.form_result.get("parent") is not None:
            page.parents.append(self.form_result.get("parent"))

        target = h.entity_url(page)  # by default, redirect to the page
        if proposal is not None and can.selection.create(proposal):
            model.Selection.create(proposal, page, c.user)
            # if a selection was created, go there instead:
            target = h.page.url(page, member='branch',
                                query={'proposal': proposal.id})

        model.meta.Session.commit()
        watchlist.check_watch(page)
        event.emit(event.T_PAGE_CREATE, c.user, instance=c.instance,
                   topics=[page], page=page, rev=page.head)
        redirect(target)

    @RequireInstance
    @validate(schema=PageEditForm(), form='edit', post_only=False, on_get=True)
    def edit(self, id, variant=None, text=None, branch=False, errors={}):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        c.variant = request.params.get("variant", c.variant)
        c.proposal = request.params.get("proposal")
        c.branch = branch

        if branch or c.variant is None:
            c.variant = ""

        require.norm.edit(c.page, c.variant)

        if branch and c.proposal:
            proposal = model.Proposal.find(c.proposal)
            if proposal:
                c.variant = libtext.variant_normalize(proposal.title)[:199]
        defaults = dict(request.params)
        c.text_rows = libtext.text_rows(c.text)
        c.left = c.page.head
        html = render('/page/edit.html')
        return htmlfill.render(html, defaults=defaults,
                               errors=errors, force_defaults=False)

    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    def update(self, id, variant=None, text=None, format='html'):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        branch = False
        try:
            class state_(object):
                page = c.page

            # branch is validated on its own, since it needs to be
            # carried to the
            # error page.
            branch_val = validators.StringBool(not_empty=False,
                                               if_empty=False,
                                               if_missing=False)
            branch = branch_val.to_python(request.params.get('branch'))

            self.form_result = PageUpdateForm().to_python(request.params,
                                                          state=state_())
            parent_text = self.form_result.get("parent_text")
            if ((branch or
                 parent_text.variant != self.form_result.get("variant")) and
                self.form_result.get("variant") in c.page.variants):
                msg = (_("Variant %s is already present, cannot branch.") %
                       self.form_result.get("variant"))
                raise Invalid(msg, branch, state_(),
                              error_dict={'variant': msg})
        except Invalid, i:
            return self.edit(id, variant=c.variant, text=c.text.id,
                             branch=branch, errors=i.unpack_errors())

        c.variant = self.form_result.get("variant")
        require.norm.edit(c.page, c.variant)

        if parent_text.page != c.page:
            return ret_abort(_("You're trying to update to a text which is "
                               "not part of this pages history"),
                             code=400, format=format)

        if can.variant.edit(c.page, model.Text.HEAD):
            parent_page = self.form_result.get("parent_page", NoPage)
            if parent_page != NoPage and parent_page != c.page:
                c.page.parent = parent_page

        if can.page.manage(c.page):
            c.page.milestone = self.form_result.get('milestone')

        if not branch and c.variant != parent_text.variant \
            and parent_text.variant != model.Text.HEAD:
            c.page.rename_variant(parent_text.variant, c.variant)

        text = model.Text.create(c.page, c.variant, c.user,
                                 self.form_result.get("title"),
                                 self.form_result.get("text"),
                                 parent=parent_text)

        target = text
        proposal = self.form_result.get("proposal")
        if proposal is not None and can.selection.create(proposal):
            target = model.Selection.create(proposal, c.page, c.user)
            poll = target.variant_poll(c.variant)
            if poll and can.poll.vote(poll):
                decision = democracy.Decision(c.user, poll)
                decision.make(model.Vote.YES)
                model.Tally.create_from_poll(poll)

        model.meta.Session.commit()
        watchlist.check_watch(c.page)
        event.emit(event.T_PAGE_EDIT, c.user, instance=c.instance,
                   topics=[c.page], page=c.page, rev=text)
        redirect(h.entity_url(target))

    @RequireInstance
    def show(self, id, variant=None, text=None, format='html'):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        require.page.show(c.page)
        if c.text.variant != c.variant:
            abort(404, _("Variant %s does not exist!") % c.variant)
        if format == 'json':
            return render_json(c.page.to_dict(text=c.text))
        if c.variant != model.Text.HEAD:
            options = [c.page.variant_head(v) for v in c.page.variants]
            return self._differ(c.page.head, c.text, options=options)
        c.tile = tiles.page.PageTile(c.page)

        sorts = {_("oldest"): sorting.entity_oldest,
                 _("newest"): sorting.entity_newest,
                 _("alphabetically"): sorting.delegateable_title}
        c.subpages_pager = pager.NamedPager(
            'subpages', c.page.subpages, tiles.page.smallrow, sorts=sorts,
            default_sort=sorting.delegateable_title)
        self._common_metadata(c.page, c.text)
        return render("/page/show.html")

    @RequireInstance
    def history(self, id, variant=model.Text.HEAD, text=None, format='html'):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, text)
        require.page.show(c.page)
        if c.text is None:
            h.flash(_("No such text revision."), 'notice')
            redirect(h.entity_url(c.page))
        c.texts_pager = pager.NamedPager(
            'texts', c.text.history, tiles.text.history_row, count=10,
            sorts={_("oldest"): sorting.entity_oldest,
                   _("newest"): sorting.entity_newest},
            default_sort=sorting.entity_newest)
        if format == 'json':
            return render_json(c.texts_pager)
        c.tile = tiles.page.PageTile(c.page)
        self._common_metadata(c.page, c.text)
        return render('/page/history.html')

    @RequireInstance
    @validate(schema=PageDiffForm(), form='bad_request', post_only=False,
              on_get=True)
    def diff(self):
        left = self.form_result.get('left')
        right = self.form_result.get('right')
        options = [right.page.variant_head(v) for v in right.page.variants]
        return self._differ(left, right, options=options)

    def _differ(self, left, right, options=None):
        if left == right:
            h.flash(_("Cannot compare identical text revisions."), 'notice')
            redirect(h.entity_url(right))
        c.left, c.right = (left, right)
        c.left_options = options
        require.page.show(c.right.page)
        if c.left.page != c.right.page:
            h.flash(_("Cannot compare versions of different texts."), 'notice')
            redirect(h.entity_url(c.right))
        c.tile = tiles.page.PageTile(c.right.page)
        self._common_metadata(c.right.page, c.right)
        return render("/page/diff.html")

    @RequireInstance
    def ask_purge(self, id, variant):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, None)
        require.variant.delete(c.page, c.variant)
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/ask_purge.html")

    @RequireInstance
    @RequireInternalRequest()
    def purge(self, id, variant):
        c.page, c.text, c.variant = self._get_page_and_text(id, variant, None)
        require.variant.delete(c.page, c.variant)
        c.page.purge_variant(c.variant)
        model.meta.Session.commit()
        #event.emit(event.T_PAGE_DELETE, c.user, instance=c.instance,
        #           topics=[c.page], page=c.page)
        h.flash(_("The variant %s has been deleted.") % c.variant,
                'success')
        redirect(h.entity_url(c.page))

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
        h.flash(_("The page %s has been deleted.") % c.page.title,
                'success')
        redirect(h.entity_url(c.page.instance))

    def _get_page_and_text(self, id, variant, text):
        page = get_entity_or_abort(model.Page, id)
        _text = page.head
        if text is not None:
            _text = get_entity_or_abort(model.Text, text)
            if _text.page != page or (variant and _text.variant != variant):
                abort(404, _("Invalid text ID %s for this page/variant!") %
                      text)
            variant = _text.variant
        elif variant is not None:
            _text = page.variant_head(variant)
            if _text is None:
                _text = page.head
        else:
            variant = _text.variant
        return (page, _text, variant)

    def _common_metadata(self, page, text):
        if text and text.text and len(text.text):
            h.add_meta("description",
                       libtext.meta_escape(text.text, markdown=False)[0:160])
        tags = page.tags
        if len(tags):
            h.add_meta("keywords", ", ".join([k.name for (k, v) in tags]))
        h.add_meta("dc.title",
                   libtext.meta_escape(page.title, markdown=False))
        h.add_meta("dc.date",
                   page.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author",
                   libtext.meta_escape(text.user.name, markdown=False))
