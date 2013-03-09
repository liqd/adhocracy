import logging

from pylons import tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

from adhocracy.lib.base import BaseController
from adhocracy.lib.static import get_static_page
from adhocracy.lib.templating import render

log = logging.getLogger(__name__)


class StaticController(BaseController):

    def serve(self, page_name, format='html'):
        c.static = get_static_page(page_name)
        c.active_global_nav = page_name
        if c.static is None:
            abort(404, _('The requested page was not found'))
        if format == 'simple':
            ret = render('/plain_doc.html')
        else:
            ret = render('/template_doc.html')
        return ret
