import urllib
import math
import re
import os.path 

from BeautifulSoup import BeautifulSoup

from pylons.templating import render_mako, render_mako_def
from pylons.i18n import _
from pylons import request, tmpl_context as c

import formencode
from formencode import foreach, validators, htmlfill

import tiles
import util
import text

def tpl_vars():
    vars = dict()
    vars['tiles'] = tiles
    return vars


def render(template_name, extra_vars=None, cache_key=None, 
               cache_type=None, cache_expire=None):
    """
    Signature matches that of pylons actual render_mako. 
    """
    if not extra_vars:
        extra_vars = {}
    
    extra_vars.update(tpl_vars())
    
    return render_mako(template_name, extra_vars=extra_vars, 
                       cache_key=cache_key, cache_type=cache_type,
                       cache_expire=cache_expire)
    
def render_def(template_name, def_name, extra_vars=None, cache_key=None, 
               cache_type=None, cache_expire=None, **kwargs):
    """
    Signature matches that of pylons actual render_mako_def. 
    """
    if not extra_vars:
        extra_vars = {}
    
    extra_vars.update(tpl_vars())
    extra_vars.update(kwargs)
    
    return render_mako_def(template_name, def_name,  
                           cache_key=cache_key, cache_type=cache_type,
                           cache_expire=cache_expire, **extra_vars)
    
class NamedPager(object): 
    """
    A ``NamedPager`` is a list generator for the UI. The ``name`` is required
    in order to distinguish multiple pagers working on the same page.  
    """
    
    def __init__(self, name, items, itemfunc, count=10, sorts={}, default_sort=None, **kwargs):
        self.name = name
        self._items = []
        for i in items: # stable set() - fugly, can this be done differently? 
            if not i in self._items:
                self._items.append(i) 
        self.itemfunc = itemfunc
        self.count = count
        self.sorts = sorts
        if len(sorts.values()):
            self.selected_sort = sorts.values().index(default_sort) + 1
        else:
            self.selected_sort = 0
        self.sorted = False
        self.kwargs = kwargs
        self._parse_request()
        
    def _parse_request(self):
        page_val = validators.Int(if_empty=1, not_empty=False)
        self.page = page_val.to_python(request.params.get("%s_page" % self.name))
        
        count_val = validators.Int(if_empty=self.count, if_invalid=self.count, 
                                   max=250, not_empty=False)
        self.count = count_val.to_python(request.params.get("%s_count" % self.name))       
        
        sort_val = validators.Int(if_empty=self.selected_sort, if_invalid=self.selected_sort, 
                                  min=1, max=len(self.sorts.keys()), not_empty=False)
        self.selected_sort = sort_val.to_python(request.params.get("%s_sort" % self.name))
                
    def _get_items(self):
        if not self.sorted and len(self.sorts.values()):
            sorter = self.sorts.values()[self.selected_sort - 1]
            self._items = sorter(self._items)
            self.sorted = True
        
        offset = (self.page-1)*self.count
        return self._items[offset:offset+self.count]
    
    items = property(_get_items)
        
    def pages(self):
        return int(math.ceil(len(self._items)/float(self.count)))
    
    def rel_page(self, step=1):
        cand = self.page + step
        return cand if cand > 0 and cand <= self.pages() else None
    
    def serialize(self, page=None, count=None, sort=None):
        query = dict()
        query.update(request.params)
        query.update(self.kwargs)
        query["%s_page" % self.name] = page if page else self.page
        query["%s_count" % self.name] = count if count else self.count
        query["%s_sort" % self.name] = sort if sort else self.selected_sort
        return "?" + urllib.urlencode(query.items())
    
    def here(self):
        return render_def('/pager.html', 'namedpager', pager=self)
        
    def __len__(self):
        return len(self.items)
    
    

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
        if path is not None: return self._load(path)
        
        path = util.get_site_path(self.DIR, fmt % text.i18n.DEFAULT.language)
        if path is not None: return self._load(path)
        
        path = util.get_path(self.DIR, fmt % c.locale.language)
        if path is not None: return self._load(path)
        
        path = util.get_path(self.DIR, fmt % text.i18n.DEFAULT.language)
        if path is not None: return self._load(path)
            
    
    def _load(self, path):
        basedir = util.get_site_path(self.DIR)
        if not os.path.abspath(path).startswith(basedir):
            return 
        
        page_content = file(path, 'r').read()
        page_soup = BeautifulSoup(page_content)
        
        body = page_soup.findAll('body', limit=1)[0].contents
        self.body = "".join(map(unicode,body))
        title = page_soup.findAll('title', limit=1)[0].contents
        self.title = "".join(map(unicode,title))
        self.exists = True
        
