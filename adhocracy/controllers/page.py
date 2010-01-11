import os, os.path
import re

from BeautifulSoup import BeautifulSoup

from pylons.i18n import _, get_lang

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

VALID_PAGE = re.compile("^[a-zA-Z0-9\_\-]*$")
STATIC_PATH = os.path.join(config.get('here'), 'adhocracy', 'page')

class PageController(BaseController):
    
    def serve(self, page_name):
        c.page = StaticPage(page_name)
        if not c.page.exists:
            abort(404, _('The requested page was not found'))
        return render('/template_doc.html')
    