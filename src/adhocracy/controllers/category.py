from pylons import tmpl_context as c
from pylons.decorators import validate
from pylons.controllers.util import abort

from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, render_logo
from adhocracy.lib import helpers as h
from adhocracy.lib import pager
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.auth import require
from adhocracy.lib.staticpage import add_static_content
from adhocracy.lib.util import get_entity_or_abort
from adhocracy import model

from proposal import ProposalFilterForm


class CategoryController(BaseController):

    identifier = 'category'

    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def show(self, id):
        if not c.instance.display_category_pages:
            abort(404)
        require.proposal.index()
        query = self.form_result.get('proposals_q')

        category = get_entity_or_abort(model.CategoryBadge, id)

        categories = model.CategoryBadge.all(instance=c.instance)

        pages = model.Page.all_q(instance=c.instance,
                                 functions=model.Page.LISTED) \
            .join(model.DelegateableBadges) \
            .filter(model.DelegateableBadges.badge_id == category.id) \
            .all()
        pages = filter(lambda p: p.parent is None, pages)
        pages_pager = pager.pages(pages,
                                  enable_pages=False,
                                  enable_sorts=False)

        proposals_pager = pager.solr_proposal_pager(
            c.instance,
            {'text': query},
            extra_filter={'facet.delegateable.badgecategory': category.id})

        data = {
            'category': category,
            'categories': categories,
            'pages_pager': pages_pager,
            'proposals_pager': proposals_pager,
        }
        return render('/category/show.html', data,
                      overlay=format == u'overlay')

    @RequireInstance
    def index(self):
        if not c.instance.display_category_pages:
            abort(404)
        data = {
            'categories': h.category.get_sorted_categories(c.instance)
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
