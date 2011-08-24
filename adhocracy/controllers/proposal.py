import logging
from operator import attrgetter

import formencode
from formencode import htmlfill, Invalid, validators

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _

from repoze.what.plugins.pylonshq import ActionProtector

from adhocracy import forms, model
from adhocracy.lib import democracy, event, helpers as h, pager
from adhocracy.lib import search as libsearch, tiles, watchlist
from adhocracy.lib.auth import authorization, can, csrf, require
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render, render_json
from adhocracy.lib.queue import post_update
from adhocracy.lib.util import get_entity_or_abort

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
    tags = validators.String(max=20000, not_empty=False)
    milestone = forms.MaybeMilestone(if_empty=None,
            if_missing=None)
    page = formencode.foreach.ForEach(PageInclusionForm())


class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True


class ProposalUpdateForm(ProposalEditForm):
    label = forms.UnusedTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    wiki = validators.StringBool(not_empty=False, if_empty=False,
                                 if_missing=False)
    milestone = forms.MaybeMilestone(if_empty=None,
            if_missing=None)


class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False,
                                    if_empty=None, if_missing=None)
    proposals_state = validators.String(max=255, not_empty=False,
                                        if_empty=None, if_missing=None)


class DelegateableBadgesForm(formencode.Schema):
    allow_extra_fields = True
    badge = formencode.foreach.ForEach(forms.ValidBadge())

    

class ProposalController(BaseController):

    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        require.proposal.index()
        query = self.form_result.get('proposals_q')
        proposals = libsearch.query.run(query, instance=c.instance,
                                        entity_type=model.Proposal)

        if self.form_result.get('proposals_state'):
            proposals = model.Proposal.filter_by_state(
                self.form_result.get('proposals_state'), proposals)
        c.proposals_pager = pager.proposals(proposals)

        if format == 'json':
            return render_json(c.proposals_pager)

        tags = model.Tag.popular_tags(limit=30)
        c.cloud_tags = sorted(text.tag_cloud_normalize(tags),
                              key=lambda (k, c, v): k.name)
        c.tile = tiles.instance.InstanceTile(c.instance)
        return render("/proposal/index.html")

    @RequireInstance
    @validate(schema=ProposalNewForm(), form='bad_request',
              post_only=False, on_get=True)
    def new(self, errors=None):
        require.proposal.create()
        c.pages = []
        c.exclude_pages = []
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
                                        wiki=self.form_result.get('wiki'))
        description.parents = [proposal]
        model.meta.Session.flush()
        proposal.description = description

        for page in self.form_result.get('page', []):
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
            target = model.Selection.create(proposal, page, c.user)
            poll = target.variant_poll(variant)
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
        c.can_edit_wiki = self._can_edit_wiki(c.proposal, c.user)
        require.proposal.edit(c.proposal)

        c.text_rows = text.text_rows(c.proposal.description.head)
        return htmlfill.render(render("/proposal/edit.html"),
                               defaults=dict(request.params),
                               errors=errors, force_defaults=False)

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
        self._common_metadata(c.proposal)
        return render("/proposal/show.html")

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
        events = model.Event.find_by_topic(c.proposal)

        if format == 'rss':
            return event.rss_feed(
                events, _("Proposal: %s") % c.proposal.title,
                h.entity_url(c.proposal),
                description=_("Activity on the %s proposal") % c.proposal.title
                )

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
        proposals = libsearch.query.run(query, instance=c.instance,
                                     entity_type=model.Proposal)
        c.proposals_pager = pager.proposals(proposals)
        return c.proposals_pager.here()

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

    @ActionProtector(authorization.has_permission("global.admin"))
    def badges(self, id, errors=None):
        c.badges = model.Badge.all()
        c.badges = filter(lambda x: x.badge_delegateable, c.badges)
        c.badges = sorted(c.badges, key=attrgetter('title'))
        c.proposal = get_entity_or_abort(model.Proposal, id)
        defaults = {'badge': [str(badge.id) for badge in c.proposal.badges]}
        return formencode.htmlfill.render(
            render("/proposal/badges.html"),
            defaults=defaults)

    @RequireInternalRequest()
    @validate(schema=DelegateableBadgesForm(), form='badges')
    @ActionProtector(authorization.has_permission("global.admin"))
    def update_badges(self, id):
        proposal = get_entity_or_abort(model.Proposal, id)
        badges = self.form_result.get('badge')
        creator = c.user

        added = []
        removed = []
        for badge in proposal.badges:
            if badge not in badges:
                removed.append(badge)
                proposal.badges.remove(badge)

        for badge in badges:
            if badge not in proposal.badges:
                model.DelegateableBadge(proposal, badge, creator)
                added.append(badge)

        model.meta.Session.commit()
        post_update(proposal, model.update.UPDATE)
        redirect(h.entity_url(proposal))   


                                          
