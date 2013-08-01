import logging

import formencode

from pylons import tmpl_context as c
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy.lib import search as libsearch, sorting, tiles
from adhocracy.lib.auth import guard
from adhocracy.lib.base import BaseController
from adhocracy.lib.pager import NamedPager
from adhocracy.lib.templating import render
from adhocracy.model import Comment

log = logging.getLogger(__name__)


class SearchQueryForm(formencode.Schema):
    allow_extra_fields = True
    serp_q = formencode.validators.String(max=255, min=1, if_empty="",
                                          if_missing="", not_empty=False)


class SearchController(BaseController):

    def _search_form(self):
        return render("search/results.html")

    @guard.proposal.index()
    @validate(schema=SearchQueryForm(), form="_search_form",
              post_only=False, on_get=True)
    def query(self):
        c.query = self.form_result.get("serp_q", u"*:*")
        self._query_pager()
        return formencode.htmlfill.render(render("search/results.html"),
                                          {'q': c.query, 'serp_q': c.query})

    @guard.proposal.index()
    @validate(schema=SearchQueryForm(), post_only=False, on_get=True)
    def filter(self):
        c.query = self.form_result.get("serp_q", '')
        self._query_pager()
        return c.entities_pager.here()

    def _query_pager(self):
        instance = c.instance if c.instance else None
        c.entities = libsearch.query.run(c.query, instance=instance,
                                         excluded_entity_types=set([Comment]))
        c.entities_pager = NamedPager(
            'serp', c.entities, tiles.dispatch_row,
            sorts={_("oldest"): sorting.entity_oldest,
                   _("newest"): sorting.entity_newest,
                   _("relevance"): sorting.entity_stable},
            default_sort=sorting.entity_stable,
            q=c.query)
