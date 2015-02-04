import logging
import urllib

import formencode
from formencode import htmlfill, Invalid, validators

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import config
from adhocracy import forms, model
from adhocracy.lib import democracy, event, helpers as h, pager
from adhocracy.lib import sorting, tiles, watchlist
from adhocracy.lib import votedetail
from adhocracy.lib.auth import authorization, can, csrf, require, guard
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render, render_def, render_json, ret_abort
from adhocracy.lib.templating import OVERLAY_SMALL
from adhocracy.lib.queue import update_entity
from adhocracy.lib.util import get_entity_or_abort
from adhocracy.lib.util import split_filter
from adhocracy.lib.text import title2alias
from adhocracy.lib.text import variant_normalize

import adhocracy.lib.text as text


log = logging.getLogger(__name__)


class ProposalNewForm(formencode.Schema):
    allow_extra_fields = True


class PageInclusionForm(formencode.Schema):
    id = forms.ValidPage()
    text = validators.String(max=20000, min=0, if_empty="")


class ProposalCreateForm(ProposalNewForm):
    pre_validators = [formencode.variabledecode.NestedVariables()]
    title = forms.ValidProposalTitle(unused_label=True)
    text = validators.String(max=20000, min=4, not_empty=True)
    tags = validators.String(max=20000, not_empty=False, if_missing=None)
    amendment = validators.StringBool(not_empty=False, if_empty=False,
                                      if_missing=False)
    milestone = forms.MaybeMilestone(if_empty=None,
                                     if_missing=None)
    page = formencode.foreach.ForEach(PageInclusionForm())
    category = formencode.foreach.ForEach(forms.ValidCategoryBadge())
    watch = validators.StringBool(not_empty=False, if_empty=False,
                                  if_missing=False)
    wiki = validators.StringBool(not_empty=False, if_empty=False,
                                 if_missing=False)


class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True


class ProposalUpdateForm(ProposalEditForm):
    title = forms.ValidProposalTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    wiki = validators.StringBool(not_empty=False, if_empty=False,
                                 if_missing=False)
    frozen = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)
    milestone = forms.MaybeMilestone(if_empty=None,
                                     if_missing=None)
    category = formencode.foreach.ForEach(forms.ValidCategoryBadge())
    watch = validators.StringBool(not_empty=False, if_empty=False,
                                  if_missing=False)
    badge = formencode.foreach.ForEach(forms.ValidDelegateableBadge())
    thumbnailbadge = formencode.foreach.ForEach(forms.ValidThumbnailBadge())


class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False,
                                    if_empty=None, if_missing=None)
    proposals_state = validators.String(max=255, not_empty=False,
                                        if_empty=None, if_missing=None)


class DelegateableBadgesForm(formencode.Schema):
    allow_extra_fields = True
    badge = formencode.foreach.ForEach(forms.ValidDelegateableBadge())
    thumbnailbadge = formencode.foreach.ForEach(forms.ValidThumbnailBadge())


class ProposalController(BaseController):

    identifier = 'proposals'

    def __init__(self):
        super(ProposalController, self).__init__()

    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        require.proposal.index()
        query = self.form_result.get('proposals_q')

        # FIXME: Add tag filtering again (now solr based)
        # FIXME: Live filtering ignores selected facets.
        c.proposals_pager = pager.solr_proposal_pager(
            c.instance,
            {'text': query})

        if format == 'json':
            return render_json(c.proposals_pager)

        c.tile = tiles.instance.InstanceTile(c.instance)
        c.tutorial_intro = _('tutorial_proposal_overview_tab')
        c.tutorial = 'proposal_index'

        if format == 'overlay':
            return render("/proposal/index.html", overlay=True)
        else:
            return render("/proposal/index.html")

    def _set_categories(self):
        categories = model.CategoryBadge.all(
            c.instance, include_global=not c.instance.hide_global_categories)

        toplevel, lowerlevel = split_filter(lambda c: c.parent is None,
                                            categories)

        # If there is exactly one top level category and there are lower
        # level categories, only these are shown in the category chooser,
        # and the (single) toplevel select description is used as the toplevel
        # select prompt.

        if len(toplevel) == 1 and len(lowerlevel) > 0:
            categories = lowerlevel
            c.toplevel_question = toplevel[0].select_child_description
            root = toplevel[0]
        else:
            c.toplevel_question = None
            root = None

        c.categories = sorted(
            [(cat.id, cat.get_key(root), cat.select_child_description)
             for cat in categories],
            key=lambda x: x[1])

    @RequireInstance
    @guard.proposal.create()
    @validate(schema=ProposalNewForm(), form='bad_request',
              post_only=False, on_get=True)
    def new(self, errors=None, page=None, amendment=False, format='html'):
        c.pages = []
        c.exclude_pages = []
        c.amendment = bool(amendment)
        if c.amendment:
            c.page = get_entity_or_abort(model.Page, page)

        if c.amendment and not c.page.allow_selection:
            return ret_abort(
                _("Page %s does not allow selections") % c.page.title,
                code=400, format=format)

        if h.site.is_local_url(request.params.get(u'cancel_url', u'')):
            c.cancel_url = request.params['cancel_url']
        elif amendment:
            c.cancel_url = h.entity_url(c.page, member='amendment')
        else:
            c.cancel_url = h.base_url('/proposal')

        self._set_categories()

        if 'category' in request.params:
            badge = model.CategoryBadge.find(request.params['category'])
            if badge is not None:
                c.selected_category = (badge.id, badge.title)

        def append_page(pid, text=None):
            page = model.Page.find(pid)
            if (page
                and page not in c.exclude_pages
                and page.function == model.Page.NORM
                and (page.allow_selection
                     or c.instance.allow_propose_changes)):
                c.pages.append((page.id, page.title,
                                page.head.text if text is None else text))
                c.exclude_pages.append(page)

        if page is not None:
            append_page(page)
        if 'page' in request.params:
            append_page(request.params.get('page'))

        try:
            val = formencode.variabledecode.NestedVariables()
            form = val.to_python(request.params)
            for pg in form.get('page', []):
                append_page(pg.get('id'), pg.get('text'))
        except:
            pass

        if c.instance.use_norms and c.instance.allow_propose_changes:
            q = model.meta.Session.query(model.Page)
            q = q.filter(model.Page.function == model.Page.NORM)
            q = q.filter(model.Page.instance == c.instance)
            q = q.filter(model.Page.allow_selection == False)  # noqa
            c.exclude_pages += q.all()
            c.can_select = True
        else:
            c.can_select = False

        defaults = dict(request.params)
        if not defaults:
            defaults['watch'] = True
            defaults['wiki'] = c.instance.editable_proposals_default

        return htmlfill.render(render("/proposal/new.html",
                                      overlay=format == u'overlay'),
                               defaults=defaults, errors=errors,
                               force_defaults=False)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @guard.proposal.create()
    def create(self, page=None, format='html', amendment=False):
        """amendment does only indicate if this controller was called from
        the amendment route. The information about wether this will be an
        amendment or classic proposal must be given in the form."""

        try:
            self.form_result = ProposalCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors(), page=page,
                            amendment=amendment)

        title = self.form_result.get('title')
        label = title2alias(title)
        variant = variant_normalize(title)

        is_amendment = self.form_result.get('amendment', False)

        proposal = model.Proposal.create(c.instance,
                                         label,
                                         c.user, with_vote=can.user.vote(),
                                         tags=self.form_result.get("tags"),
                                         is_amendment=is_amendment)
        proposal.milestone = self.form_result.get('milestone')
        model.meta.Session.flush()
        description = model.Page.create(c.instance,
                                        title,
                                        self.form_result.get('text'),
                                        c.user,
                                        function=model.Page.DESCRIPTION,
                                        wiki=self.form_result.get('wiki'),
                                        formatting=True)
        description.parents = [proposal]
        model.meta.Session.flush()
        proposal.description = description

        categories = self.form_result.get('category')
        category = categories[0] if categories else None
        proposal.set_category(category, c.user)

        def valid_page(item):
            page = item.get('id')
            return page is not None and \
                page.function == model.Page.NORM and \
                can.norm.edit(page, variant) and \
                can.selection.create(proposal)

        _pages = self.form_result.get('page', [])
        pages = filter(valid_page, _pages)

        if ((is_amendment and len(pages) != 1) or
                any([not p['id'].allow_selection for p in pages]) or
                (not is_amendment and not c.instance.allow_propose_changes and
                    len(pages) != 0)):
            if is_amendment and len(pages) != 1:
                log.warning(
                    u'Could not create amendment: Not the right number of '
                    u'valid pages in %s -> %s' % (_pages, pages))
            model.meta.Session.rollback()
            return self.new(
                errors={u'msg':
                        u'Cannot change arbitrary norms within proposals'})

        if c.instance.require_selection and len(pages) < 1:
            h.flash(
                _('Please select norm and propose a change to it.'),
                'error')
            model.meta.Session.rollback()
            return self.new()

        for _page in pages:
            page_text = _page.get('text', '')
            page = _page['id']
            model.Text.create(page, variant, c.user,
                              page.head.title,
                              page_text, parent=page.head)
            selection = model.Selection.create(proposal, page, c.user,
                                               variant=variant)
            poll = selection.variant_poll(variant)
            if poll and can.poll.vote(poll):
                decision = democracy.Decision(c.user, poll)
                decision.make(model.Vote.YES)
                model.Tally.create_from_poll(poll)

        model.meta.Session.commit()
        if can.watch.create():
            watchlist.set_watch(proposal, self.form_result.get('watch'))
        if is_amendment:
            event.emit(event.T_AMENDMENT_CREATE, c.user, instance=c.instance,
                       topics=[proposal, page], proposal=proposal,
                       rev=description.head, page=page)
        else:
            event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance,
                       topics=[proposal], proposal=proposal,
                       rev=description.head)
        redirect(h.entity_url(proposal, format=format, in_overlay=False))

    @RequireInstance
    @validate(schema=ProposalEditForm(), form="bad_request",
              post_only=False, on_get=True)
    def edit(self, id, errors={}, page=None, format=u'html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        c.badges = self._editable_badges(c.proposal)
        c.thumbnailbadges = self._editable_thumbnailbadges(c.proposal)
        require.proposal.edit(c.proposal)
        c.can_edit_wiki = self._can_edit_wiki(c.proposal, c.user)

        c.text_rows = text.text_rows(c.proposal.description.head)

        self._set_categories()

        # categories for this proposal
        # (single category not assured in db model)
        c.category = c.proposal.category

        force_defaults = False
        if errors:
            force_defaults = True
        defaults = dict(request.POST)
        if not defaults:
            # Just clicked on edit
            defaults['watch'] = h.find_watch(c.proposal) is not None
            defaults['frozen'] = c.proposal.frozen
        defaults.update({"category": c.category.id if c.category else None})
        return htmlfill.render(render("/proposal/edit.html",
                                      overlay=format == u'overlay',
                                      overlay_size=OVERLAY_SMALL),
                               defaults=defaults,
                               errors=errors, force_defaults=force_defaults)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    def update(self, id, format='html'):
        try:
            c.proposal = get_entity_or_abort(model.Proposal, id)

            class state_(object):
                page = c.proposal.description

            self.form_result = ProposalUpdateForm().to_python(request.params,
                                                              state=state_())

            badges = self.form_result.get('badge')
            thumbnailbadges = self.form_result.get('thumbnailbadge')
        except Invalid, i:
            return self.edit(id, errors=i.unpack_errors())

        require.proposal.edit(c.proposal)

        c.proposal.milestone = self.form_result.get('milestone')
        model.meta.Session.add(c.proposal)

        if not config.get_bool('adhocracy.proposal.split_badge_edit'):
            added, removed = self._update_badges(badges, thumbnailbadges,
                                                 c.proposal)
        else:
            added = removed = []

        # change the category
        categories = self.form_result.get('category')
        category = categories[0] if categories else None
        c.proposal.set_category(category, c.user)

        if self._can_edit_wiki(c.proposal, c.user):
            wiki = self.form_result.get('wiki')
        else:
            wiki = c.proposal.description.head.wiki

        if h.has_permission('proposal.freeze'):
            c.proposal.frozen = self.form_result.get('frozen')

        _text = model.Text.create(c.proposal.description, model.Text.HEAD,
                                  c.user,
                                  self.form_result.get('title'),
                                  self.form_result.get('text'),
                                  parent=c.proposal.description.head,
                                  wiki=wiki)
        model.meta.Session.commit()
        if can.watch.create():
            watchlist.set_watch(c.proposal, self.form_result.get('watch'))
        if c.proposal.is_amendment:
            page = c.proposal.selection.page
            event.emit(event.T_AMENDMENT_EDIT, c.user, instance=c.instance,
                       topics=[c.proposal, page], proposal=c.proposal,
                       page=page, rev=_text,
                       badges_added=added, badges_removed=removed)
        else:
            event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance,
                       topics=[c.proposal], proposal=c.proposal, rev=_text,
                       badges_added=added, badges_removed=removed)
        redirect(h.entity_url(c.proposal, format=format, in_overlay=False))

    @RequireInstance
    def show(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)

        c.num_selections = c.proposal.selections
        c.show_selections = (c.proposal.instance.use_norms
                             and c.proposal.instance.allow_propose_changes)
        if c.show_selections:
            c.sorted_selections = sorting.sortable_text(
                c.proposal.selections,
                key=lambda s: s.page.title)

        if votedetail.is_enabled():
            c.votedetail = votedetail.calc_votedetail_dict(
                c.instance, c.proposal.rate_poll)

        if format == 'rss':
            return self.activity(id, format)
        elif format == 'json':
            return render_json(c.proposal)

        c.tile = tiles.proposal.ProposalTile(c.proposal)
        used_pages = [selection.page for selection in c.proposal.selections]
        functions = [model.Page.NORM]
        available_pages = model.Page.all(instance=c.instance,
                                         exclude=used_pages,
                                         functions=functions)
        c.disable_include = len(available_pages) == 0
        c.history_url = h.entity_url(c.proposal.description.head,
                                     member='history')
        c.category = c.proposal.category
        self._common_metadata(c.proposal)
        c.tutorial_intro = _('tutorial_proposal_show_tab')
        c.tutorial = 'proposal_show'
        monitor_comment_behavior = config.get_bool(
            'adhocracy.monitor_comment_behavior')
        if monitor_comment_behavior:
            c.monitor_comment_url = '%s?%s' % (
                h.base_url('/stats/read_comments'),
                urllib.urlencode({'path':
                                  h.entity_url(c.proposal).encode('utf-8')}))

        if format == 'overlay':
            return render("/proposal/show.html", overlay=True)
        else:
            return render("/proposal/show.html")

    @RequireInstance
    def comments(self, id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)
        c.page = c.proposal.description

        if format == u'overlay':
            c.came_from = h.entity_url(c.proposal,
                                       member='comments',
                                       in_overlay=False,
                                       format='overlay')
            return render("/page/comments.html", overlay=True,
                          overlay_size=OVERLAY_SMALL)
        else:
            return render("/page/comments.html")

    @RequireInstance
    def history(self, id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)

        proposal_text = c.proposal.description.head
        c.texts_pager = pager.NamedPager(
            'texts', proposal_text.history, tiles.text.history_row, count=10,
            sorts={_("oldest"): sorting.entity_oldest,
                   _("newest"): sorting.entity_newest},
            default_sort=sorting.entity_newest)

        self._common_metadata(c.proposal)
        if format == 'ajax':
            return render_def('/proposal/history.html', 'content')
        elif format == 'overlay':
            return render('/proposal/history.html', overlay=True,
                          overlay_size=OVERLAY_SMALL)
        else:
            return render('/proposal/history.html')

    @RequireInstance
    def delegations(self, id, format="html"):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)
        delegations = c.proposal.current_delegations()
        c.delegations_pager = pager.delegations(delegations)

        if format == 'json':
            return render_json(c.delegations_pager)

        c.tile = tiles.proposal.ProposalTile(c.proposal)
        self._common_metadata(c.proposal)
        if format == 'overlay':
            return render("/proposal/delegations.html", overlay=True)
        else:
            return render("/proposal/delegations.html")

    @RequireInstance
    def activity(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)

        if format == 'rss':
            events = model.Event.find_by_topic(c.proposal, limit=50)
            return event.rss_feed(
                events, _("Proposal: %s") % c.proposal.title,
                h.entity_url(c.proposal),
                description=_("Activity on the %s proposal") % c.proposal.title
            )

        events = model.Event.find_by_topic(c.proposal)
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        c.events_pager = pager.events(events)
        self._common_metadata(c.proposal)
        if format == 'overlay':
            return render("/proposal/activity.html", overlay=True)
        else:
            return render("/proposal/activity.html")

    @RequireInstance
    def ask_delete(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.delete(c.proposal)
        c.tile = tiles.proposal.ProposalTile(c.proposal)

        if format == 'overlay':
            return render('/proposal/ask_delete.html', overlay=True)
        else:
            return render('/proposal/ask_delete.html')

    @RequireInstance
    @csrf.RequireInternalRequest()
    def delete(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.delete(c.proposal)
        if c.proposal.is_amendment:
            came_from = h.entity_url(c.proposal.selection.page,
                                     member='amendment')
            page = c.proposal.selection.page
            event.emit(event.T_AMENDMENT_DELETE, c.user, instance=c.instance,
                       topics=[c.proposal, page], proposal=c.proposal,
                       page=page)
        else:
            came_from = h.entity_url(c.instance)
            event.emit(event.T_PROPOSAL_DELETE, c.user, instance=c.instance,
                       topics=[c.proposal], proposal=c.proposal)
        c.proposal.delete()
        model.meta.Session.commit()
        h.flash(_("The proposal %s has been deleted.") % c.proposal.title,
                'success')
        redirect(came_from)

    @RequireInstance
    def ask_adopt(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.adopt(c.proposal)
        return render('/proposal/ask_adopt.html')

    @RequireInstance
    def adopt(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.adopt(c.proposal)
        poll = model.Poll.create(c.proposal, c.user, model.Poll.ADOPT)
        model.meta.Session.commit()
        c.proposal.adopt_poll = poll
        model.meta.Session.commit()
        event.emit(event.T_PROPOSAL_STATE_VOTING, c.user, instance=c.instance,
                   topics=[c.proposal], proposal=c.proposal, poll=poll)
        redirect(h.entity_url(c.proposal, in_overlay=False))

    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def filter(self):
        require.proposal.index()
        query = self.form_result.get('proposals_q')
        proposals_pager = pager.solr_proposal_pager(c.instance,
                                                    {'text': query})
        return render_json({'listing': proposals_pager.here(),
                            'facets': proposals_pager.render_facets()})

    def _common_metadata(self, proposal):
        h.add_meta("description",
                   text.meta_escape(proposal.description.head.text,
                                    markdown=True)[0:160])
        tags = proposal.tags
        if len(tags):
            h.add_meta("keywords", ", ".join([k.name for (k, v) in tags]))
        h.add_meta("dc.title",
                   text.meta_escape(proposal.title, markdown=False))
        h.add_meta("dc.date",
                   proposal.create_time.strftime("%Y-%m-%d"))
        h.add_meta("dc.author",
                   text.meta_escape(proposal.creator.name, markdown=False))
        h.add_rss(_("Proposal: %(proposal)s") % {'proposal': proposal.title},
                  h.entity_url(c.proposal, format='rss'))

    def _can_edit_wiki(self, proposal, user):
        if authorization.has('instance.admin'):
            return True
        if proposal.creator == user:
            return True
        return False

    @classmethod
    def _editable_badges(cls, proposal):
        '''
        Return the badges editable that can be assigned by the current
        user.
        '''
        badges = []
        if can.proposal.edit_badges(proposal):
            badges.extend(model.DelegateableBadge.all(instance=c.instance))
            badges.extend(model.DelegateableBadge.all(instance=None))
        badges = sorted(badges, key=lambda badge: badge.title)
        return badges

    @classmethod
    def _editable_thumbnailbadges(cls, proposal):
        '''
        Return the thumbnailbadges editable that can be assigned by the current
        user.
        '''
        thumbnailbadges = []
        if can.proposal.edit_badges(proposal):
            thumbnailbadges.extend(
                model.ThumbnailBadge.all(instance=c.instance))
            thumbnailbadges.extend(model.ThumbnailBadge.all(instance=None))
        thumbnailbadges = sorted(thumbnailbadges,
                                 key=lambda badge: badge.title)
        return thumbnailbadges

    def badges(self, id, errors=None, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.edit_badges(c.proposal)
        c.badges = self._editable_badges(c.proposal)
        c.thumbnailbadges = self._editable_thumbnailbadges(c.proposal)
        default_thumbnail = c.proposal.thumbnails and \
            c.proposal.thumbnails[0].id or ''
        defaults = {'badge': [str(badge.id) for badge in c.proposal.badges],
                    '_tok': csrf.token_id(),
                    'thumbnailbadge': default_thumbnail,
                    }
        return formencode.htmlfill.render(
            render("/proposal/badges.html", overlay=format == u'overlay',
                   overlay_size=OVERLAY_SMALL),
            defaults=defaults)

    def _update_badges(self, badges, thumbnailbadges, proposal):
        editable_badges = self._editable_badges(proposal)
        editable_badges.extend(self._editable_thumbnailbadges(c.proposal))
        added = []
        removed = []

        for badge in badges + thumbnailbadges:
            if badge not in editable_badges:
                ret_abort(_(u"You are not allowed to edit badge %i")
                          % badge.id, code=403)

        for badge in proposal.badges:
            if badge not in badges:
                removed.append(badge)
                proposal.badges.remove(badge)
        for badge in proposal.thumbnails:
            if badge not in thumbnailbadges:
                removed.append(badge)
                proposal.thumbnails.remove(badge)

        for badge in badges + thumbnailbadges:
            if badge not in proposal.badges + proposal.thumbnails:
                badge.assign(proposal, c.user)
                added.append(badge)

        if added or removed:
            # FIXME: needs commit() cause we do a redirect() which raises
            # an Exception.
            model.meta.Session.commit()
            update_entity(proposal, model.UPDATE)

        return added, removed

    @RequireInternalRequest()
    @validate(schema=DelegateableBadgesForm(), form='badges')
    @csrf.RequireInternalRequest(methods=['POST'])
    def update_badges(self, id, format='html'):
        proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.edit_badges(proposal)
        badges = self.form_result.get('badge')
        thumbnailbadges = self.form_result.get('thumbnailbadge')
        redirect_to_proposals = self.form_result.get('redirect_to_proposals')

        added, removed = self._update_badges(badges, thumbnailbadges, proposal)
        if added or removed:
            event.emit(event.T_PROPOSAL_BADGE, c.user, instance=c.instance,
                       topics=[proposal], proposal=proposal,
                       badges_added=added, badges_removed=removed)

        if format == 'ajax':
            obj = {'badges_html': render_def('/badge/tiles.html', 'badges',
                                             badges=proposal.badges),
                   'thumbnailbadges_html': render_def(
                       '/badge/tiles.html', 'badges',
                       badges=proposal.thumbnails),
                   }
            return render_json(obj)
        elif redirect_to_proposals:
            redirect("/proposal")
        else:
            redirect(h.entity_url(proposal))
