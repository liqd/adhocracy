from datetime import date, datetime, time
import logging

import formencode
from formencode import htmlfill, Invalid, validators

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import config
from adhocracy import forms, model
from adhocracy.lib import helpers as h, pager, tiles, watchlist
from adhocracy.lib.auth import can
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
    category = forms.ValidCategoryBadge(if_missing=None, if_empty=None)
    show_all_proposals = validators.StringBool(not_empty=False, if_empty=False,
                                               if_missing=False)
    time = forms.ValidDate(not_empty=True)
    watch = validators.StringBool(not_empty=False, if_empty=False,
                                  if_missing=False)


class MilestoneEditForm(formencode.Schema):
    allow_extra_fields = True


class MilestoneUpdateForm(MilestoneEditForm):
    title = validators.String(max=2000, min=4, not_empty=True)
    text = validators.String(max=60000, min=4, not_empty=True)
    category = forms.ValidCategoryBadge(if_missing=None, if_empty=None)
    show_all_proposals = validators.StringBool(not_empty=False, if_empty=False,
                                               if_missing=False)
    time = forms.ValidDate(not_empty=True)
    watch = validators.StringBool(not_empty=False, if_empty=False,
                                  if_missing=False)


class MilestoneController(BaseController):

    identifier = 'milestones'

    @RequireInstance
    def index(self, format="html"):
        require.milestone.index()

        milestones = model.Milestone.all(instance=c.instance)
        broken = [m for m in milestones if m.time is None]
        for milestone in broken:
            log.warning('Time of Milestone is None: %s' %
                        h.entity_url(milestone))
        milestones = [m for m in milestones if m.time is not None]
        today = datetime.combine(date.today(), time(0, 0))
        past_milestones = [m for m in milestones if m.time < today]
        c.show_past_milestones = len(past_milestones)
        c.past_milestones_pager = pager.milestones(past_milestones)

        current_milestones = [m for m in milestones if m not in
                              past_milestones]
        c.show_current_milestones = (bool(current_milestones)
                                     or not c.show_past_milestones)
        c.current_milestones_pager = pager.milestones(current_milestones)
        c.milestones = past_milestones + current_milestones  # for the timeline
        if format == 'json':
            return render_json(c.milestones_pager)

        c.tile = tiles.instance.InstanceTile(c.instance)
        c.tutorial = 'milestone_index'
        c.tutorial_intro = _('tutorial_milestones_tab')
        if format == 'overlay':
            return render("/milestone/index.html", overlay=True)
        else:
            return render("/milestone/index.html")

    @RequireInstance
    @validate(schema=MilestoneNewForm(), form='bad_request',
              post_only=False, on_get=True)
    def new(self, errors=None, format=u'html'):
        require.milestone.create()
        c.categories = model.CategoryBadge.all(instance=c.instance)
        defaults = dict(request.params)
        if not defaults:
            defaults['watch'] = True
        return htmlfill.render(render("/milestone/new.html",
                                      overlay=format == u'overlay'),
                               defaults=defaults, errors=errors,
                               force_defaults=False)

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    def create(self, format='html'):
        require.milestone.create()
        c.categories = model.CategoryBadge.all(instance=c.instance)
        try:
            self.form_result = MilestoneCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors())

        category = self.form_result.get('category')
        milestone = model.Milestone.create(c.instance, c.user,
                                           self.form_result.get("title"),
                                           self.form_result.get('text'),
                                           self.form_result.get('time'),
                                           category=category)
        if config.get_bool('adhocracy.milestone.allow_show_all_proposals'):
            milestone.show_all_proposals = self.form_result.get(
                'show_all_proposals')

        model.meta.Session.commit()
        if can.watch.create():
            watchlist.set_watch(milestone, self.form_result.get('watch'))
        # event.emit(event.T_PROPOSAL_CREATE, c.user, instance=c.instance,
        #            topics=[proposal], proposal=proposal,
        #            rev=description.head)
        redirect(h.entity_url(milestone, format=format))

    @RequireInstance
    @validate(schema=MilestoneEditForm(), form="bad_request",
              post_only=False, on_get=True)
    def edit(self, id, errors={}):
        c.categories = model.CategoryBadge.all(instance=c.instance)
        c.milestone = get_entity_or_abort(model.Milestone, id)
        require.milestone.edit(c.milestone)
        defaults = {'category': (str(c.milestone.category.id) if
                                 c.milestone.category else None),
                    'show_all_proposals': c.milestone.show_all_proposals,
                    'watch': h.find_watch(c.milestone),
                    }
        defaults.update(dict(request.params))
        return htmlfill.render(render("/milestone/edit.html"),
                               defaults=defaults,
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
        c.milestone.category = self.form_result.get('category')
        c.milestone.time = self.form_result.get('time')
        if config.get_bool('adhocracy.milestone.allow_show_all_proposals'):
            c.milestone.show_all_proposals = self.form_result.get(
                'show_all_proposals')
        model.meta.Session.commit()
        if can.watch.create():
            watchlist.set_watch(c.milestone, self.form_result.get('watch'))
        # event.emit(event.T_PROPOSAL_EDIT, c.user, instance=c.instance,
        #            topics=[c.proposal], proposal=c.proposal, rev=_text)
        redirect(h.entity_url(c.milestone))

    @RequireInstance
    def show(self, id, format='html'):
        c.milestone = get_entity_or_abort(model.Milestone, id)
        require.milestone.show(c.milestone)

        if format == 'json':
            return render_json(c.milestone)

        c.tile = tiles.milestone.MilestoneTile(c.milestone)

        extra_filter = {}
        alternatives_filter = {}

        if (config.get_bool('adhocracy.milestone.allow_show_all_proposals')
           and c.milestone.show_all_proposals
           and not c.milestone.over):
            extra_filter['facet.delegateable.frozen'] = False
        else:

            # proposals .. directly assigned
            alternatives_filter['facet.delegateable.milestones']\
                = c.milestone.id

            # proposals .. with the same category
            if c.milestone.category:
                alternatives_filter['facet.delegateable.badgecategory']\
                    = c.milestone.category.id

        c.proposals_pager = pager.solr_proposal_pager(
            c.instance, extra_filter=extra_filter,
            alternatives_filter=alternatives_filter)

        c.show_proposals_pager = bool(c.proposals_pager.total_num_items())

        # pages
        pages = model.Page.by_milestone(c.milestone,
                                        instance=c.instance,
                                        include_deleted=False,
                                        functions=[model.Page.NORM])
        c.pages_pager = pager.pages(pages, size=20, enable_sorts=False)
        c.show_pages_pager = len(pages) and c.instance.use_norms

        self._common_metadata(c.milestone)
        c.tutorial_intro = _('tutorial_milestone_details_tab')
        c.tutorial = 'milestone_show'

        return render("/milestone/show.html", overlay=(format == 'overlay'))

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
        # event.emit(event.T_milestone_DELETE, c.user, instance=c.instance,
        #            topics=[c.milestone], milestone=c.milestone)
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
                   (milestone.time and milestone.time.strftime("%Y-%m-%d") or
                    ''))
        h.add_meta("dc.author",
                   text.meta_escape(milestone.creator.name, markdown=False))
