from util import render_tile, BaseTile

from pylons import request, response, session, tmpl_context as c
from pylons.i18n import _ 

from webhelpers.text import truncate

import adhocracy.model as model
from .. import helpers as h
from .. import text

class UserTile(BaseTile):
    
    def __init__(self, user):
        self.user = user
        self.__instance_group = None
   
    def _bio(self):       
        if self.user.bio:
            return text.render(self.user.bio)
        return ""
    
    bio = property(_bio)
    
    def _tagline(self):       
        if self.user.bio:
            tagline = text.plain(self.user.bio)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    def _can_edit(self):
        return (h.has_permission("user.edit") and c.user == self.user) \
                 or h.has_permission("user.manage")
    
    can_edit = property(_can_edit)
      
    def _can_manage(self):
        return h.has_permission("instance.admin")
    
    can_manage = property(_can_manage) 
        
    def _num_issues(self):
        pred = lambda d: isinstance(d, model.Issue) and \
                         d.instance==c.instance and \
                         not d.is_deleted()
        return len(filter(pred, self.user.delegateables))
    
    num_issues = property(_num_issues)
    
    def _num_proposals(self):
        pred = lambda d: isinstance(d, model.Proposal) and \
                         d.instance==c.instance and \
                         not d.is_deleted()
        return len(filter(pred, self.user.delegateables))
    
    num_proposals = property(_num_proposals)
    
    def _num_comments(self):
        pred = lambda cm: cm.topic.instance == c.instance and \
                          not cm.is_deleted()
        return len(filter(pred, self.user.comments))
    
    num_comments = property(_num_comments)
    
    def _num_instances(self):
        return len([i for i in self.user.instances if i.is_shown()])
    
    num_instances = property(_num_instances)
    
    def karmas(self):
        return filter(lambda k: k.comment.topic.instance == c.instance, self.user.karma_received)
    
    def _num_karma_up(self):
        return len(filter(lambda k: k.value > 0, self.karmas()))
    
    num_karma_up = property(_num_karma_up)
    
    def _num_karma_down(self):
        return len(filter(lambda k: k.value < 0, self.karmas()))
    
    num_karma_down = property(_num_karma_down)
    
    def _instance_group(self):
        if c.instance and not self.__instance_group:     
            m = self.user.instance_membership(c.instance)
            self.__instance_group = m.group if m else None
        return self.__instance_group
        
    instance_group = property(_instance_group)

def row(user):
    return render_tile('/user/tiles.html', 'row', UserTile(user), 
                       user=user, instance=c.instance, cached=True)   

def header(user, tile=None, active='activity'):
    if tile is None:
        tile = UserTile(user)
    return render_tile('/user/tiles.html', 'header', tile, 
                       user=user, active=active)