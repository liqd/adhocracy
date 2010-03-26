import urllib
import math

import formencode
from formencode import foreach, validators, htmlfill

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
    
    def __init__(self, name, items, itemfunc, count=10, sorts={}, default_sort=None, **kwargs):
        self.name = name
        self._items = []
        for i in items: # stable set() - fugly, can this be done differently? 
            if not i in self._items:
                self._items.append(i) 
        self.itemfunc = itemfunc
        self.count = self.initial_count = count
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
    
    
    def serialize(self, page=None, count=None, sort=None, **kwargs):
        query = dict(request.params.items())
        query.update(self.kwargs)
        query.update(kwargs)
        query["%s_page" % self.name] = page if page else self.page
        query["%s_count" % self.name] = count if count else self.count
        query["%s_sort" % self.name] = sort if sort else self.selected_sort
        
        query = dict([(str(k), unicode(v).encode('utf-8')) \
                      for k, v in query.items()])
        return "?" + urllib.urlencode(query.items())
    
    
    def here(self):
        return render_def('/pager.html', 'namedpager', pager=self)
    
        
    def __len__(self):
        return len(self.items)



def instances(instances):
    return NamedPager('instances', instances, tiles.instance.row,
                      sorts={_("oldest"): sorting.entity_oldest,
                             _("newest"): sorting.entity_newest,
                             _("activity"): sorting.instance_activity,
                             _("name"): sorting.delegateable_label},
                      default_sort=sorting.instance_activity)

  
def issues(issues, has_query=False):
    sorts = {_("oldest"): sorting.entity_oldest,
             _("newest"): sorting.entity_newest,
             _("activity"): sorting.issue_activity,
             _("newest comment"): sorting.delegateable_latest_comment,
              _("name"): sorting.delegateable_label}
        
    return NamedPager('issues', issues, tiles.issue.row, sorts=sorts,
                      default_sort=sorting.issue_activity)

  
def proposals(proposals, has_query=False, detail=True):
    sorts = {_("oldest"): sorting.entity_oldest,
             #_("newest"): sorting.entity_newest,
             _("activity"): sorting.proposal_activity,
             _("newest comment"): sorting.delegateable_latest_comment,
             _("support"): sorting.proposal_support,
              _("name"): sorting.delegateable_label}
    return NamedPager('proposals', proposals, tiles.proposal.row, sorts=sorts,
                      default_sort=sorting.proposal_support)
                      
                      
def users(users, has_query=False):
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
    return NamedPager('events', events, tiles.event.row, count=10)
