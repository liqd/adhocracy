from pylons import request, tmpl_context as c
from pylons.decorators import validate
from pylons.controllers.util import redirect, abort
from pylons.i18n import _

from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, ret_abort, render_png
from adhocracy.lib import helpers as h, logo, pager
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.auth import require
from adhocracy.lib.util import get_entity_or_abort
from adhocracy import model

from proposal import ProposalFilterForm


class CategoryController(BaseController):
    def __init__(self):
        super(CategoryController, self).__init__()
        c.active_subheader_nav = 'category'

    @RequireInstance
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def show(self, id):
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
        pages_pager = pager.pages(pages,
                                  enable_pages=False,
                                  enable_sorts=False)

        proposals_pager = pager.solr_proposal_pager(
            c.instance,
            {'text': query},
            extra_filter={'facet.delegateable.badgecategory': category.id})

        data = {
            'category': category,
            'pages_pager': pages_pager,
            'proposals_pager': proposals_pager,
        }
        return render('/category/show.html', data,
                      overlay=format == u'overlay')

    @RequireInstance
    def index(self):
        if not c.instance.display_category_pages:
            abort(404)
        c.categories = model.CategoryBadge.all(instance=c.instance,
                                               visible_only=True)
        c.categories = filter(lambda c: len(c.children) == 0, c.categories)
        return render('/category/index.html', overlay=format == u'overlay')

    @RequireInstance
    def image(self, id, y, x=None):
        if not c.instance.display_category_pages:
            abort(404)
        category = get_entity_or_abort(model.CategoryBadge, id)
        if not logo.exists(category):
            return ret_abort(
                _(u"No image for category '%s'.") % category.title, code=404)
        (x, y) = logo.validate_xy(x, y)
        (path, mtime, io) = logo.load(category, size=(x, y))
        request_mtime = int(request.params.get('t', 0))
        if request_mtime > mtime:
            # This will set the appropriate mtime
            redirect(h.category.image_url(category, y, x=x))
        return render_png(io, mtime, cache_forever=True)
