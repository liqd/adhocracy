import logging
import urllib

import formencode
from formencode import htmlfill, Invalid, validators

from paste.deploy.converters import asbool

from pylons import config, request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import forms, model
from adhocracy.lib import democracy, event, helpers as h, pager
from adhocracy.lib import sorting, tiles, watchlist
from adhocracy.lib.auth import authorization, can, csrf, require, guard
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render, render_def, render_json
from adhocracy.lib.queue import update_entity
from adhocracy.lib.util import get_entity_or_abort
from adhocracy.lib.util import split_filter

import adhocracy.lib.text as text


log = logging.getLogger(__name__)


class ProposalNewForm(formencode.Schema):
    allow_extra_fields = True


class PageInclusionForm(formencode.Schema):
    id = forms.ValidPage()
    text = validators.String(max=20000, min=0, if_empty="")


class ProposalCreateForm(ProposalNewForm):
    pre_validators = [formencode.variabledecode.NestedVariables()]
    label = forms.UnusedTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    tags = validators.String(max=20000, not_empty=False, if_missing=None)
    milestone = forms.MaybeMilestone(if_empty=None,
                                     if_missing=None)
    page = formencode.foreach.ForEach(PageInclusionForm())
    category = formencode.foreach.ForEach(forms.ValidCategoryBadge())


class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True


class ProposalUpdateForm(ProposalEditForm):
    label = forms.UnusedTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    wiki = validators.StringBool(not_empty=False, if_empty=False,
                                 if_missing=False)
    milestone = forms.MaybeMilestone(if_empty=None,
                                     if_missing=None)
    category = formencode.foreach.ForEach(forms.ValidCategoryBadge())


class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False,
                                    if_empty=None, if_missing=None)
    proposals_state = validators.String(max=255, not_empty=False,
                                        if_empty=None, if_missing=None)


class DelegateableBadgesForm(formencode.Schema):
    allow_extra_fields = True
    badge = formencode.foreach.ForEach(forms.ValidDelegateableBadge())


class ProposalController(BaseController):

    def __init__(self):
        super(ProposalController, self).__init__()
        c.active_subheader_nav = 'proposals'

    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        require.proposal.index()
        query = self.form_result.get('proposals_q')

        # FIXME: Add tag filtering again (now solr based)
        # FIXME: Live filtering ignores selected facets.
        def_sort = None
        if c.user and c.user.proposal_sort_order:
            def_sort = c.user.proposal_sort_order
        c.proposals_pager = pager.solr_proposal_pager(c.instance,
                                                      {'text': query},
                                                      default_sorting=def_sort)

        if format == 'json':
            return render_json(c.proposals_pager)

        c.tile = tiles.instance.InstanceTile(c.instance)
        c.tutorial_intro = _('tutorial_proposal_overview_tab')
        c.tutorial = 'proposal_index'
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
    def new(self, errors=None):
        c.pages = []
        c.exclude_pages = []

        self._set_categories()

        if 'page' in request.params:
            page = model.Page.find(request.params.get('page'))
            if page and page.function == model.Page.NORM:
                c.pages.append((page.id, page.title, page.head.text))
                c.exclude_pages.append(page)
        try:
            val = formencode.variabledecode.NestedVariables()
            form = val.to_python(request.params)
            for pg in form.get('page', []):
                page = model.Page.find(pg.get('id'))
                if page and page.function == model.Page.NORM:
                    c.pages.append((page.id, page.title, pg.get('text')))
                    c.exclude_pages.append(page)
        except:
            pass
        defaults = dict(request.params)
        defaults['watch'] = defaults.get('watch', True)
        return htmlfill.render(render("/proposal/new.html"),
                               defaults=defaults, errors=errors,
                               force_defaults=False)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    def create(self, format='html'):
        require.proposal.create()

        try:
            self.form_result = ProposalCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors())

        pages = self.form_result.get('page', [])
        if c.instance.require_selection and len(pages) < 1:
            h.flash(
                _('Please select norm and propose a change to it.'),
                'error')
            return self.new()
        proposal = model.Proposal.create(c.instance,
                                         self.form_result.get("label"),
                                         c.user, with_vote=can.user.vote(),
                                         tags=self.form_result.get("tags"))
        proposal.milestone = self.form_result.get('milestone')
        model.meta.Session.flush()
        description = model.Page.create(c.instance,
                                        self.form_result.get("label"),
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

        for page in pages:
            page_text = page.get('text', '')
            page = page.get('id')
            if page is None or page.function != model.Page.NORM:
                continue
            var_val = forms.VariantName()
            variant = var_val.to_python(self.form_result.get('label'))
            if not can.norm.edit(page, variant) or \
                    not can.selection.create(proposal):
                continue
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
        watchlist.check_watch(proposal)
        event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance,
                   topics=[proposal], proposal=proposal, rev=description.head)
        redirect(h.entity_url(proposal, format=format))

    @RequireInstance
    @validate(schema=ProposalEditForm(), form="bad_request",
              post_only=False, on_get=True)
    def edit(self, id, errors={}):
        c.proposal = get_entity_or_abort(model.Proposal, id)
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
        defaults = dict(request.params)
        defaults.update({"category": c.category.id if c.category else None})
        return htmlfill.render(render("/proposal/edit.html"),
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
        except Invalid, i:
            return self.edit(id, errors=i.unpack_errors())

        require.proposal.edit(c.proposal)

        c.proposal.label = self.form_result.get('label')
        c.proposal.milestone = self.form_result.get('milestone')
        model.meta.Session.add(c.proposal)

        # change the category
        categories = self.form_result.get('category')
        category = categories[0] if categories else None
        c.proposal.set_category(category, c.user)

        if self._can_edit_wiki(c.proposal, c.user):
            wiki = self.form_result.get('wiki')
        else:
            wiki = c.proposal.description.head.wiki
        _text = model.Text.create(c.proposal.description, model.Text.HEAD,
                                  c.user,
                                  self.form_result.get('label'),
                                  self.form_result.get('text'),
                                  parent=c.proposal.description.head,
                                  wiki=wiki)
        model.meta.Session.commit()
        watchlist.check_watch(c.proposal)
        event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance,
                   topics=[c.proposal], proposal=c.proposal, rev=_text)
        redirect(h.entity_url(c.proposal))

    @RequireInstance
    def show(self, id, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.show(c.proposal)

        c.num_selections = c.proposal.selections
        c.show_selections = c.proposal.instance.use_norms
        if c.show_selections:
            c.sorted_selections = sorting.sortable_text(
                c.proposal.selections,
                key=lambda s: s.page.title)

        if format == 'rss':
            return self.activity(id, format)

        if format == 'json':
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
        monitor_comment_behavior = asbool(
            config.get('adhocracy.monitor_comment_behavior', 'False'))
        if monitor_comment_behavior:
            c.monitor_comment_url = '%s?%s' % (
                h.base_url('/stats/read_comments'),
                urllib.urlencode({'path': h.entity_url(c.proposal)}))
        return render("/proposal/show.html")

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
        if format == 'overlay':
            return render_def('/proposal/history.html', 'overlay_content')
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
        return render("/proposal/activity.html")

    @RequireInstance
    def ask_delete(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.delete(c.proposal)
        c.tile = tiles.proposal.ProposalTile(c.proposal)
        return render('/proposal/ask_delete.html')

    @RequireInstance
    @csrf.RequireInternalRequest()
    def delete(self, id):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        require.proposal.delete(c.proposal)
        event.emit(event.T_PROPOSAL_DELETE, c.user, instance=c.instance,
                   topics=[c.proposal], proposal=c.proposal)
        c.proposal.delete()
        model.meta.Session.commit()
        h.flash(_("The proposal %s has been deleted.") % c.proposal.title,
                'success')
        redirect(h.entity_url(c.instance))

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
        redirect(h.entity_url(c.proposal))

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
        if can.badge.edit_instance():
            badges.extend(model.DelegateableBadge.all(instance=c.instance))
        if can.badge.edit_global():
            badges.extend(model.DelegateableBadge.all(instance=None))
        badges = sorted(badges, key=lambda badge: badge.title)
        return badges

    @guard.perm("instance.admin")
    def badges(self, id, errors=None, format='html'):
        c.proposal = get_entity_or_abort(model.Proposal, id)
        c.badges = self._editable_badges(c.proposal)
        defaults = {
            'badge': [str(badge.id) for badge in c.proposal.badges],
            '_tok': csrf.token_id()
        }
        if format == 'ajax':
            checked = [badge.id for badge in c.proposal.badges]
            json = {'title': c.proposal.title,
                    'badges': [{
                        'id': badge.id,
                        'description': badge.description,
                        'title': badge.title,
                        'checked': badge.id in checked} for badge in c.badges]}
            return render_json(json)

        return formencode.htmlfill.render(
            render("/proposal/badges.html"),
            defaults=defaults)

    @RequireInternalRequest()
    @validate(schema=DelegateableBadgesForm(), form='badges')
    @guard.perm("instance.admin")
    @csrf.RequireInternalRequest(methods=['POST'])
    def update_badges(self, id, format='html'):
        proposal = get_entity_or_abort(model.Proposal, id)
        editable_badges = self._editable_badges(proposal)
        badges = self.form_result.get('badge')
        redirect_to_proposals = self.form_result.get('redirect_to_proposals')

        added = []
        removed = []

        for badge in proposal.badges:
            if badge not in editable_badges:
                # the user can not edit the badge, so we don't remove it
                continue
            if badge not in badges:
                removed.append(badge)
                proposal.badges.remove(badge)

        for badge in badges:
            if badge not in proposal.badges:
                badge.assign(proposal, c.user)
                added.append(badge)

        # FIXME: needs commit() cause we do an redirect() which raises
        # an Exception.
        model.meta.Session.commit()
        update_entity(proposal, model.update.UPDATE)
        if format == 'ajax':
            obj = {'html': render_def('/badge/tiles.html', 'badges',
                                      badges=proposal.badges)}
            return render_json(obj)
        if redirect_to_proposals:
            redirect("/proposal")
        redirect(h.entity_url(proposal))
