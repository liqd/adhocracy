from pylons import request
from pylons.controllers.util import redirect
from pylons.i18n import _

from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import ret_abort, render_png
from adhocracy.lib import helpers as h, logo
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.util import get_entity_or_abort
from adhocracy import model


class CategoryController(BaseController):
    def __init__(self):
        super(CategoryController, self).__init__()
        c.active_subheader_nav = 'category'

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
