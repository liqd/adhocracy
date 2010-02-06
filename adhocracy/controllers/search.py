from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.model as model
from formencode.validators import RequireIfMissing

log = logging.getLogger(__name__)

class SearchQueryForm(formencode.Schema):
    allow_extra_fields = True
    serp_q = validators.String(max=255, min=1, if_empty="", if_missing="", not_empty=False)

class SearchController(BaseController):
    
    @ActionProtector(has_permission("proposal.view"))
    def search_form(self):
        return render("search/results.html")
    
    @ActionProtector(has_permission("proposal.view"))
    @validate(schema=SearchQueryForm(), form="search_form", post_only=False, on_get=True)
    def query(self):
        c.query = self.form_result.get("serp_q") 
        self._query_pager()
        return formencode.htmlfill.render(render("search/results.html"),
                        {'q': c.query, 'serp_q': c.query})
    
    @ActionProtector(has_permission("proposal.view"))
    @validate(schema=SearchQueryForm(), post_only=False, on_get=True)
    def filter(self):
        c.query = self.form_result.get("serp_q", '') + '*' 
        self._query_pager()
        return c.entities_pager.here()
    
    
    def _query_pager(self):
        c.entities = libsearch.query.run(c.query, instance=c.instance if c.instance else None)
        c.entities = filter(lambda e: not isinstance(e, model.Comment), c.entities)
        c.entities_pager = NamedPager('serp', c.entities, tiles.dispatch_row, 
                                      sorts={_("oldest"): sorting.entity_oldest,
                                             _("newest"): sorting.entity_newest,
                                             _("relevance"): sorting.entity_stable},
                                      default_sort=sorting.entity_stable,
                                      q=c.query)
        
