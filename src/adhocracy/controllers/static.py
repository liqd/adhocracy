import logging
from time import time

from pylons import tmpl_context as c
from pylons.controllers.util import abort
from pylons.i18n import _

from adhocracy.lib.base import BaseController
from adhocracy.lib.static import StaticPage
from adhocracy.lib.templating import render

log = logging.getLogger(__name__)


class StaticController(BaseController):

    def serve(self, page_name, format='html'):
        begin_time = time()
        c.static = StaticPage(page_name)
        c.active_global_nav = page_name
        if not c.static.exists:
            abort(404, _('The requested page was not found'))
        if format == 'simple':
            ret = render('/plain_doc.html')
        else:
            ret = render('/template_doc.html')
        ms = (time() - begin_time) * 1000
        log.debug("Rendering static %s took %sms" % (page_name, ms))
        return ret
