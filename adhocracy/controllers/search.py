from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.model as model

log = logging.getLogger(__name__)

class SearchQueryForm(formencode.Schema):
    allow_extra_fields = True
    q = validators.String(max=255, min=1, not_empty=True)

class SearchController(BaseController):
    
    @ActionProtector(has_permission("proposal.view"))
    def query(self):
        try:
            c.query = SearchQueryForm().to_python(request.params).get("q")
            c.entities = libsearch.query.run(c.query, instance=c.instance if c.instance else None)
            c.entities = filter(lambda e: not isinstance(e, model.Comment), c.entities)
            c.entities_pager = NamedPager('serp', c.entities, tiles.dispatch_row, q=c.query)
        except formencode.Invalid:
            h.flash(_("Received no query for search."))
                
        return formencode.htmlfill.render(render("search/results.html"),
                        {'q': c.query})
