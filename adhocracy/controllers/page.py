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
        if not VALID_PAGE.match(page_name):
            abort(404, _('The requested page was not found'))
        
        page_path = os.path.join(STATIC_PATH, "%s.%s.html" % (page_name.lower(), get_lang()))
        if not os.path.exists(page_path):
            page_path = os.path.join(STATIC_PATH, '%s.html' % page_name.lower())
            if os.path.exists(page_path):
                log.debug("Page '%s' needs to be localized to %s" % (page_name.lower(), get_lang()))
            else:            
                abort(404, _('The requested page was not found'))
        
        page_content = file(page_path, 'r').read()
        page_soup = BeautifulSoup(page_content)
        
        c.page_text = "".join(map(unicode,page_soup.findAll('body', limit=1)[0].contents))
        c.page_title = "".join(map(unicode,page_soup.findAll('title', limit=1)[0].contents))
        
        return render('/template_doc.html')
    