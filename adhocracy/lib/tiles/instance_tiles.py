from util import render_tile, BaseTile
from datetime import timedelta

from pylons import tmpl_context as c

from webhelpers.text import truncate
from .. import text
from .. import authorization as auth
from .. import helpers as h


from category_tiles import CategoryTile

class InstanceTile(CategoryTile):
    
    def __init__(self, instance):
        self.instance = instance
        self.__issues = None
        CategoryTile.__init__(self, instance.root)
        
    def _tagline(self):       
        if self.instance.description:
            tagline = text.plain(self.instance.description)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    def _description(self):
        if self.instance.description:
            return text.render(self.instance.description)
        return ""
    
    description = property(_description)
    
    def _activation_delay(self):
        return text.i18n.format_timedelta(timedelta(days=self.instance.activation_delay))
        
    activation_delay = property(_activation_delay)
    
    def _required_majority(self):
        return "%s%%" % int(self.instance.required_majority * 100)
        
    required_majority = property(_required_majority)
    
    def _can_join(self):
        return (c.user and not c.user.is_member(self.instance)) \
                and h.has_permission("instance.join")
    
    can_join = property(_can_join)
    
    def _can_leave(self):
        return c.user and c.user.is_member(self.instance) \
                and h.has_permission("instance.leave") \
                and not c.user == self.instance.creator 
    
    can_leave = property(_can_leave)
    can_admin = property(BaseTile.prop_has_perm('instance.admin'))

def list_item(instance):
    return render_tile('/instance/tiles.html', 'list_item', 
                       InstanceTile(instance), instance=instance)

def row(instance):
    return render_tile('/instance/tiles.html', 'row', InstanceTile(instance), instance=instance)
