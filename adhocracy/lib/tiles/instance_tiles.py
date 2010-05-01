from util import render_tile, BaseTile
from datetime import timedelta

from pylons import tmpl_context as c

from webhelpers.text import truncate
from .. import text
from ..auth import authorization as auth
from .. import helpers as h

import adhocracy.model as model


class InstanceTile(BaseTile):
    
    def __init__(self, instance):
        self.instance = instance
        self.__issues = None
        self.__proposals_count = None
     
     
    @property  
    def tagline(self):       
        if self.instance.description:
            tagline = text.plain(self.instance.description)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    
    @property
    def description(self):
        if self.instance.description:
            return text.render(self.instance.description)
        return ""
    
    
    @property
    def activation_delay(self):
        return self.instance.activation_delay
    
    
    @property
    def required_majority(self):
        return "%s%%" % int(self.instance.required_majority * 100)
    
    
    @property
    def num_proposals(self):
        if self.__proposals_count is None:
            query = model.meta.Session.query(model.Proposal)
            query = query.filter(model.Proposal.instance==self.instance)
            query = query.filter(model.Proposal.delete_time==None)
            self.__proposals_count = query.count()
        return self.__proposals_count
    


def row(instance):
    return render_tile('/instance/tiles.html', 'row', InstanceTile(instance), 
                       instance=instance, user=c.user, cached=True)
    
def header(instance, tile=None, active='issues', no_panel=False):
    if tile is None:
        tile = InstanceTile(instance)
    return render_tile('/instance/tiles.html', 'header', tile, 
                       instance=instance, active=active, no_panel=no_panel)
    