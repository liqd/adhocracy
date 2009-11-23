import urllib
import math

from pylons.templating import render_mako, render_mako_def
from pylons import request, tmpl_context as c

import formencode
from formencode import foreach, validators, htmlfill

import tiles

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
    
    return render_mako_def(template_name, def_name, extra_vars=extra_vars, 
                           cache_key=cache_key, cache_type=cache_type,
                           cache_expire=cache_expire, **kwargs)
    
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
        query = {"%s_page" % self.name: page if page else self.page,
                 "%s_count" % self.name: count if count else self.count,
                 "%s_sort" % self.name: sort if sort else self.selected_sort}
        self.kwargs.update(query)
        return "?" + urllib.urlencode(self.kwargs.items())
    
    def here(self):
        return render_def('/pager.html', 'namedpager', pager=self)
        