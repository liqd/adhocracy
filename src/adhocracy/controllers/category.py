from paste.deploy.converters import asbool

from sqlalchemy.orm import aliased

from pylons import tmpl_context as c
from pylons import request
from pylons.decorators import validate
from pylons.controllers.util import abort

from adhocracy.lib import helpers as h
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, render_logo
from adhocracy.lib.templating import OVERLAY_SMALL
from adhocracy.lib import pager
from adhocracy.lib import tiles
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.auth import require
from adhocracy.lib.staticpage import add_static_content
from adhocracy.lib.util import get_entity_or_abort

from adhocracy import config
from adhocracy import model

from proposal import ProposalFilterForm


class CategoryController(BaseController):

    identifier = 'category'

    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def show(self, id, format=u'html'):
        if not c.instance.display_category_pages:
            abort(404)
        require.proposal.index()
        query = self.form_result.get('proposals_q')

        category = get_entity_or_abort(model.CategoryBadge, id)

        pages = model.Page.all_q(instance=c.instance,
                                 functions=model.Page.LISTED) \
            .join(model.DelegateableBadges) \
            .filter(model.DelegateableBadges.badge_id == category.id) \
            .all()
        pages = filter(lambda p: p.parent is None, pages)
        pages_pager = pager.NamedPager('pages', pages, tiles.page.smallrow,
                                       enable_pages=False, enable_sorts=False)

        default_sorting = config.get(
            'adhocracy.listings.instance_proposal.sorting')
        proposals_pager = pager.solr_proposal_pager(
            c.instance,
            {'text': query},
            default_sorting=default_sorting,
            extra_filter={'facet.delegateable.badgecategory': category.id})

        data = {
            'category': category,
            'pages_pager': pages_pager,
            'proposals_pager': proposals_pager,
        }
        return render('/category/show.html', data,
                      overlay=format == u'overlay')

    @RequireInstance
    def index(self, format=u'html'):
        if not c.instance.display_category_pages:
            abort(404)
        categories = model.CategoryBadge.all(instance=c.instance,
                                             visible_only=True)
        data = {
            'categories': filter(lambda c: len(c.children) == 0, categories)
        }
        add_static_content(data, u'adhocracy.static.category_index_heading',
                           body_key=u'heading_text',
                           title_key=u'heading_title')
        return render('/category/index.html', data,
                      overlay=format == u'overlay')

    @RequireInstance
    def image(self, id, y, x=None):
        if not c.instance.display_category_pages:
            abort(404)
        category = get_entity_or_abort(model.CategoryBadge, id,
                                       instance_filter=False)
        return render_logo(category, y, x=x)

    @RequireInstance
    def description(self, id, format=u'html'):
        if not c.instance.display_category_pages:
            abort(404)
        category = get_entity_or_abort(model.CategoryBadge, id)

        description = category.long_description
        description = h.render(description)
        description = h.text.truncate_html(description, 65, u'&hellip;')

        data = {
            'category': category,
            'description': description,
        }
        return render('/category/description.html', data,
                      overlay=format == 'overlay',
                      overlay_size=OVERLAY_SMALL)

    @RequireInstance
    def events(self, id, format=u'html'):
        if not c.instance.display_category_pages:
            abort(404)
        category = get_entity_or_abort(model.CategoryBadge, id)

        # Get events related to this category. This is not trivial with our
        # current models. For example this query does only include one level of
        # page nesting.
        alias = aliased(model.Delegateable)

        topics = model.meta.Session.query(model.Delegateable.id)\
            .join(model.Delegateable.categories)\
            .union(model.meta.Session.query(model.Delegateable.id)
                   .join(model.Page._proposal)
                   .join(alias, alias.id == model.Proposal.id)
                   .join(alias.categories))\
            .union(model.meta.Session.query(model.Delegateable.id)
                   .join(alias, model.Delegateable.parents)
                   .join(alias.categories))\
            .distinct()\
            .filter(model.Delegateable.instance == c.instance)\
            .filter(model.CategoryBadge.id == category.id)

        events = model.Event.all_q(
            instance=c.instance,
            include_hidden=False,
            event_filter=request.params.getall('event_filter'))\
            .join(model.Event.topics)\
            .filter(model.Delegateable.id.in_(topics))\
            .order_by(model.Event.time.desc())\
            .limit(min(int(request.params.get('count', 50)), 100)).all()

        enable_sorts = asbool(request.params.get('enable_sorts', 'true'))
        enable_pages = asbool(request.params.get('enable_pages', 'true'))
        row_type = request.params.get('row_type', 'row')

        if row_type not in ['row', 'profile_row', 'sidebar_row', 'tiny_row']:
            abort(400)

        data = {
            'event_pager': pager.events(events,
                                        enable_sorts=enable_sorts,
                                        enable_pages=enable_pages,
                                        row_type=row_type),
        }
        return render('/category/events.html', data,
                      overlay=format == 'overlay',
                      overlay_size=OVERLAY_SMALL)

    @RequireInstance
    def milestones(self, id, format=u'html'):
        if not c.instance.display_category_pages:
            abort(404)
        category = get_entity_or_abort(model.CategoryBadge, id)

        milestones = model.Milestone.all_future_q(instance=c.instance)\
            .filter(model.Milestone.category_id == category.id)\
            .limit(int(request.params.get('count', 50))).all()

        enable_sorts = asbool(request.params.get('enable_sorts', 'true'))
        enable_pages = asbool(request.params.get('enable_pages', 'true'))

        data = {
            'milestone_pager': pager.milestones(milestones,
                                                enable_sorts=enable_sorts,
                                                enable_pages=enable_pages),
        }
        return render('/category/milestones.html', data,
                      overlay=format == 'overlay',
                      overlay_size=OVERLAY_SMALL)
