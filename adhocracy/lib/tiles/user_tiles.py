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