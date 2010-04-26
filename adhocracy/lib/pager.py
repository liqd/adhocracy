import urllib
import math

import formencode
from formencode import foreach, validators, htmlfill, Invalid

from pylons.i18n import _
from pylons import request, response, tmpl_context as c

from templating import render_def
import sorting
import tiles


class NamedPager(object): 
    """
    A ``NamedPager`` is a list generator for the UI. The ``name`` is required
    in order to distinguish multiple pagers working on the same page.  
    """
    
    def __init__(self, name, items, itemfunc, size=10, sorts={}, default_sort=None, **kwargs):
        self.name = name
        self._items = items
        self.itemfunc = itemfunc
        self.size = self.initial_size = size
        self.sorts = sorts
        if len(sorts.values()):
            self.selected_sort = sorts.values().index(default_sort) + 1
        else:
            self.selected_sort = 0
        self.sorted = False
        self.kwargs = kwargs
        self._parse_request()
     
      
    def _parse_request(self):
        try:
            page_val = validators.Int(min=1, not_empty=True)
            self.page = page_val.to_python(request.params.get("%s_page" % self.name))
        except: 
            self.page = 1
        
        try:
            size_val = validators.Int(min=1, max=250, not_empty=True)
            self.size = count_val.to_python(request.params.get("%s_size" % self.name))       
        except: 
            pass
        
        try:
            sort_val = validators.Int(min=1, max=len(self.sorts.keys()), not_empty=True)
            self.selected_sort = sort_val.to_python(request.params.get("%s_sort" % self.name))
        except: 
            pass
    
    
    @property        
    def items(self):
        if not self.sorted and len(self.sorts.values()):
            sorter = self.sorts.values()[self.selected_sort - 1]
            self._items = sorter(self._items)
            self.sorted = True
        return self._items[self.offset:self.offset+self.size]
    
    
    @property
    def offset(self):
        return (self.page-1)*self.size
    
    
    @property
    def pages(self):
        return int(math.ceil(len(self._items)/float(self.size)))
    
    
    def serialize(self, page=None, size=None, sort=None, **kwargs):
        query = dict(request.params.items())
        query.update(self.kwargs)
        query.update(kwargs)
        query["%s_page" % self.name] = page if page else self.page
        query["%s_size" % self.name] = size if size else self.size
        query["%s_sort" % self.name] = sort if sort else self.selected_sort
        
        query = dict([(str(k), unicode(v).encode('utf-8')) \
                      for k, v in query.items()])
        return "?" + urllib.urlencode(query.items())
    
    
    def here(self):
        return render_def('/pager.html', 'namedpager', pager=self)
    
    
    def to_dict(self):
        return self.items
    
        
    def __len__(self):
        return len(self.items)



def instances(instances):
    return NamedPager('instances', instances, tiles.instance.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest,
                             _("activity"): sorting.instance_activity,
                             _("name"): sorting.delegateable_label},
                      default_sort=sorting.instance_activity)

  
def proposals(proposals, detail=True):
    sorts = {_("oldest"): sorting.entity_oldest,
             #_("newest"): sorting.entity_newest,
             _("activity"): sorting.proposal_activity,
             _("newest comment"): sorting.delegateable_latest_comment,
             _("support"): sorting.proposal_support,
              _("name"): sorting.delegateable_label}
    return NamedPager('proposals', proposals, tiles.proposal.row, sorts=sorts,
                      default_sort=sorting.proposal_support)


def pages(pages, detail=True):
  sorts = {_("oldest"): sorting.entity_oldest,
           _("newest"): sorting.entity_newest,
           _("name"): sorting.page_title}
  return NamedPager('pages', pages, tiles.page.row, sorts=sorts,
                    default_sort=sorting.page_title)                 

      
def users(users):
    sorts={_("oldest"): sorting.entity_oldest,
           _("newest"): sorting.entity_newest,
           _("activity"): sorting.user_activity,
           _("name"): sorting.user_name}
                
    return NamedPager('users', users, tiles.user.row, sorts=sorts,
                      default_sort=sorting.user_activity)

  
def user_decisions(decisions):
    return NamedPager('decisions', decisions, tiles.decision.user_row, 
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)


def scope_decisions(decisions):
    return NamedPager('decisions', decisions, tiles.decision.scope_row, 
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)


def comments(comments):
    return NamedPager('comments', comments, tiles.comment.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)

   
def delegations(delegations):
    return NamedPager('delegations', delegations, tiles.delegation.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest},
                      default_sort=sorting.entity_newest)


def events(events):
    return NamedPager('events', events, tiles.event.row)
