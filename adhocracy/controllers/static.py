import os, os.path
import re
from time import time

from BeautifulSoup import BeautifulSoup

from pylons.i18n import _, get_lang

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

VALID_PAGE = re.compile("^[a-zA-Z0-9\_\-]*$")
STATIC_PATH = os.path.join(config.get('here'), 'adhocracy', 'page')

class StaticController(BaseController):
    
    def serve(self, page_name):
        begin_time = time()
        c.page = StaticPage(page_name)
        if not c.page.exists:
            abort(404, _('The requested page was not found'))
        h.canonical_url(h.instance_url(None, path="/page/%s.html" % page_name))
        ret = render('/template_doc.html')
        log.debug("Rendering static %s took %sms" % (page_name, ((time()-begin_time)*1000)))
        return ret