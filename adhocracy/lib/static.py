import re
import os.path

from pylons.i18n import _
from pylons import tmpl_context as c

from BeautifulSoup import BeautifulSoup

import util
import text
import adhocracy.i18n as i18n

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
            self.lookup()
    
    
    def lookup(self):
        for locale in [c.locale, i18n.get_default_locale()] + i18n.LOCALES:
            loaded = self._lookup_lang(locale.language)
            if loaded is not None:
                break
    
        
    def _lookup_lang(self, lang):
        fmt = self.name + '.%s' + self.SUFFIX
        path = util.get_path(self.DIR, fmt % lang)
        if path is not None and os.path.exists(path): 
            return self._load(path)
        return None
    
    
    def _load(self, path):
        page_content = file(path, 'r').read()
        page_soup = BeautifulSoup(page_content)
        
        body = page_soup.findAll('body', limit=1)[0].contents
        self.body = "".join(map(unicode,body))
        title = page_soup.findAll('title', limit=1)[0].contents
        self.title = "".join(map(unicode,title))
        self.exists = True
        return title

