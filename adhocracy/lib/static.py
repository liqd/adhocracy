import re
import os.path

from pylons.i18n import _
from pylons import tmpl_context as c

from BeautifulSoup import BeautifulSoup

import util
import text

class StaticPage(object):
    VALID_PAGE = re.compile("^[a-zA-Z0-9\_\-]*$")
    DIR = 'page'
    SUFFIX = '.html'
    
    def __init__(self, name):
        self.exists = False
        self.title = _("Missing page: %s") % name
        self.body = ""
        self.name = name
        if self.VALID_PAGE.match(name):
            self.find_page()
    
    def find_page(self):
        fmt = self.name + '.%s' + self.SUFFIX
        path = util.get_site_path(self.DIR, fmt % c.locale.language)
        if os.path.exists(path): 
            return self._load(path)
        
        path = util.get_site_path(self.DIR, fmt % text.i18n.DEFAULT.language)
        if os.path.exists(path): 
            return self._load(path)
        
        path = util.get_path(self.DIR, fmt % c.locale.language)
        if path is not None and os.path.exists(path): 
            return self._load(path)
        
        path = util.get_path(self.DIR, fmt % text.i18n.DEFAULT.language)
        if path is not None and os.path.exists(path): 
            return self._load(path)
            
    
    def _load(self, path):
        page_content = file(path, 'r').read()
        page_soup = BeautifulSoup(page_content)
        
        body = page_soup.findAll('body', limit=1)[0].contents
        self.body = "".join(map(unicode,body))
        title = page_soup.findAll('title', limit=1)[0].contents
        self.title = "".join(map(unicode,title))
        self.exists = True
        
