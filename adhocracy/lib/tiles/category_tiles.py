from util import render_tile, BaseTile

from pylons import request, response, session, tmpl_context as c
from webhelpers.text import truncate

import adhocracy.model as model
from .. import helpers as h
from .. import text
from .. import authorization as auth
from .. import karma

from delegateable_tiles import DelegateableTile

class CategoryTile(DelegateableTile):
    
    def __init__(self, category):
        self.category = category
        self.__issues = None
        self.__categories = None
        DelegateableTile.__init__(self, category)
    
    def _issues(self):
        if not self.__issues:
            self.__issues = list(set(self.category.search_children(recurse=True, cls=model.Issue)))
        return self.__issues
    
    issues = property(_issues)
        
    def _num_issues(self):
        return len(self.issues)
    
    num_issues = property(_num_issues)
    
    def _categories(self):
        if not self.__categories:
            self.__categories = self.category.search_children(recurse=False, cls=model.Category)
        return self.__categories
    
    categories = property(_categories)
        
    def _num_categories(self):
        return len(self.categories)
    
    num_categories = property(_num_categories)
    
    can_edit = property(DelegateableTile.prop_has_permkarma('category.edit'))
    lack_edit_karma = property(BaseTile.prop_lack_karma('category.edit'))       
    
    can_delete = property(DelegateableTile.prop_has_permkarma('category.delete'))
    lack_delete_karma = property(BaseTile.prop_lack_karma('category.delete'))
    
    can_create_issue = property(DelegateableTile.prop_has_permkarma('issue.create', allow_creator=False))
    lack_create_issue_karma = property(BaseTile.prop_lack_karma('issue.create'))
    
    can_create_category = property(DelegateableTile.prop_has_permkarma('category.create', allow_creator=False))
    lack_create_category_karma = property(BaseTile.prop_lack_karma('category.create'))
    
    def _is_root(self):
        return self.category == self.category.instance.root
    
    is_root = property(_is_root)
    
    def _tagline(self):       
        if self.category.description:
            tagline = text.plain(self.category.description)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    def _description(self):
        if self.category.description:
            return text.render(self.category.description)
        return ""
    
    description = property(_description)

def list_item(category):
    return render_tile('/category/tiles.html', 'list_item', 
                       CategoryTile(category), category=category)    

def row(category):
    return render_tile('/category/tiles.html', 'row', CategoryTile(category), category=category)

    
