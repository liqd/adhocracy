import logging

import formencode
from formencode import htmlfill, Invalid, validators

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import forms, model
from adhocracy.lib import event, helpers as h, pager, tiles, watchlist
from adhocracy.lib import search as libsearch
from adhocracy.lib.auth import authorization, can, csrf, require
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render, render_json
from adhocracy.lib.util import get_entity_or_abort

import adhocracy.lib.text as text


log = logging.getLogger(__name__)


class ProposalNewForm(formencode.Schema):
    allow_extra_fields = True


class ProposalCreateForm(ProposalNewForm):
    label = forms.UnusedTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    tags = validators.String(max=20000, not_empty=False)
    milestone = forms.MaybeMilestone()


class ProposalEditForm(formencode.Schema):
    allow_extra_fields = True


class ProposalUpdateForm(ProposalEditForm):
    label = forms.UnusedTitle()
    text = validators.String(max=20000, min=4, not_empty=True)
    wiki = validators.StringBool(not_empty=False, if_empty=False,
                                 if_missing=False)
    milestone = forms.MaybeMilestone()


class ProposalFilterForm(formencode.Schema):
    allow_extra_fields = True
    proposals_q = validators.String(max=255, not_empty=False,
                                    if_empty=None, if_missing=None)
    proposals_state = validators.String(max=255, not_empty=False,
                                        if_empty=None, if_missing=None)


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
