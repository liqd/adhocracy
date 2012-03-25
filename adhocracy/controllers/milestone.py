import logging

import formencode
from formencode import htmlfill, Invalid, validators

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import forms, model
from adhocracy.lib import helpers as h, pager, tiles, watchlist
from adhocracy.lib.auth import csrf, require
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render, render_json
from adhocracy.lib.util import get_entity_or_abort

import adhocracy.lib.text as text


log = logging.getLogger(__name__)


class MilestoneNewForm(formencode.Schema):
    allow_extra_fields = True


class MilestoneCreateForm(MilestoneNewForm):
    title = validators.String(max=2000, min=4, not_empty=True)
    text = validators.String(max=60000, min=4, not_empty=True)
    time = forms.ValidDate()


class MilestoneEditForm(formencode.Schema):
    allow_extra_fields = True


class MilestoneUpdateForm(MilestoneEditForm):
    title = validators.String(max=2000, min=4, not_empty=True)
    text = validators.String(max=60000, min=4, not_empty=True)
    time = forms.ValidDate()


class MilestoneController(BaseController):

    def __init__(self):
        super(MilestoneController, self).__init__()
        c.active_subheader_nav = 'milestones'

    @RequireInstance
    def index(self, format="html"):
        require.milestone.index()

        c.milestones = model.Milestone.all(instance=c.instance)
        broken = [m for m in c.milestones if m.time is None]
        for milestone in broken:
            log.warning('Time of Milestone is None: %s' % h.entity_url(milestone))
        c.milestones = [m for m in c.milestones if m.time is not None]
        c.milestones_pager = pager.milestones(c.milestones)

        if format == 'json':
            return render_json(c.milestones_pager)

        c.tile = tiles.instance.InstanceTile(c.instance)
        c.tutorial = 'milestone_index'
        c.tutorial_intro = _('tutorial_milestones_tab')
        return render("/milestone/index.html")

    @RequireInstance
    @validate(schema=MilestoneNewForm(), form='bad_request',
              post_only=False, on_get=True)
    def new(self, errors=None):
        require.milestone.create()
        defaults = dict(request.params)
        defaults['watch'] = defaults.get('watch', True)
        return htmlfill.render(render("/milestone/new.html"),
                               defaults=defaults, errors=errors,
                               force_defaults=False)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    def create(self, format='html'):
        require.milestone.create()
        try:
            self.form_result = MilestoneCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors())
        milestone = model.Milestone.create(c.instance, c.user,
                                         self.form_result.get("title"),
                                         self.form_result.get('text'),
                                         self.form_result.get('time'))
        model.meta.Session.commit()
        watchlist.check_watch(milestone)
        #event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance,
        #           topics=[proposal], proposal=proposal, rev=description.head)
        redirect(h.entity_url(milestone, format=format))

    @RequireInstance
    @validate(schema=MilestoneEditForm(), form="bad_request",
              post_only=False, on_get=True)
    def edit(self, id, errors={}):
        c.milestone = get_entity_or_abort(model.Milestone, id)
        require.milestone.edit(c.milestone)
        return htmlfill.render(render("/milestone/edit.html"),
                               defaults=dict(request.params),
                               errors=errors, force_defaults=False)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    def update(self, id, format='html'):
        try:
            c.milestone = get_entity_or_abort(model.Milestone, id)
            self.form_result = MilestoneUpdateForm().to_python(request.params)
        except Invalid, i:
            return self.edit(id, errors=i.unpack_errors())

        require.milestone.edit(c.milestone)

        c.milestone.title = self.form_result.get('title')
        c.milestone.text = self.form_result.get('text')
        c.milestone.time = self.form_result.get('time')
        model.meta.Session.add(c.milestone)
        model.meta.Session.commit()
        watchlist.check_watch(c.milestone)
        #event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance,
        #           topics=[c.proposal], proposal=c.proposal, rev=_text)
        redirect(h.entity_url(c.milestone))

    @RequireInstance
    def show(self, id, format='html'):
        c.milestone = get_entity_or_abort(model.Milestone, id)
        require.milestone.show(c.milestone)

        if format == 'json':
            return render_json(c.milestone)

        c.tile = tiles.milestone.MilestoneTile(c.milestone)
        proposals = model.Proposal.by_milestone(c.milestone,
                instance=c.instance)
        c.proposals_pager = pager.proposals(proposals, size=10)
        pages_q = model.meta.Session.query(model.Page)
        pages_q = pages_q.filter(model.Page.instance==c.instance)
        pages_q = pages_q.filter(model.Page.function==model.Page.NORM)
        pages_q = pages_q.filter(model.Page.milestone==c.milestone)
        c.pages_pager = pager.pages(pages_q.all(), size=10)
        self._common_metadata(c.milestone)
        c.tutorial_intro = _('tutorial_milestone_details_tab')
        c.tutorial = 'milestone_show'
        return render("/milestone/show.html")

    @RequireInstance
    def ask_delete(self, id):
        c.milestone = get_entity_or_abort(model.Milestone, id)
        require.milestone.delete(c.milestone)
        c.tile = tiles.milestone.MilestoneTile(c.milestone)
        return render('/milestone/ask_delete.html')

    @RequireInstance
    @csrf.RequireInternalRequest()
    def delete(self, id):
        c.milestone = get_entity_or_abort(model.Milestone, id)
        require.milestone.delete(c.milestone)
        #event.emit(event.T_milestone_DELETE, c.user, instance=c.instance,
        #           topics=[c.milestone], milestone=c.milestone)
        c.milestone.delete()
        model.meta.Session.commit()
        h.flash(_("The milestone %s has been deleted.") % c.milestone.title,
                'success')
        redirect(h.entity_url(c.instance))

    def _common_metadata(self, milestone):
        h.add_meta("description",
                   text.meta_escape(milestone.text,
                                    markdown=False)[0:160])
        h.add_meta("dc.title",
                   text.meta_escape(milestone.title, markdown=False))
        h.add_meta("dc.date",
                   milestone.time and milestone.time.strftime("%Y-%m-%d") or '')
        h.add_meta("dc.author",
                   text.meta_escape(milestone.creator.name, markdown=False))

