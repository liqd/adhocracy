from util import render_tile, BaseTile
from datetime import timedelta

from pylons import tmpl_context as c

from webhelpers.text import truncate
from .. import text
from .. import authorization as auth
from .. import helpers as h

import adhocracy.model as model


class InstanceTile(BaseTile):
    
    def __init__(self, instance):
        self.instance = instance
        self.__issues = None
        
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
        return self.instance.activation_delay
        
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
    
    def _can_create_proposal(self):
        return c.user and h.has_permission("proposal.create")
    
    can_create_proposal = property(_can_create_proposal)
    
    def _num_issues(self):
        query = model.meta.Session.query(model.Issue)
        query = query.filter(model.Issue.instance==self.instance)
        query = query.filter(model.Issue.delete_time==None)
        return query.count()
    
    num_issues = property(_num_issues)
    
    def _num_proposals(self):
        query = model.meta.Session.query(model.Proposal)
        query = query.filter(model.Proposal.instance==self.instance)
        query = query.filter(model.Proposal.delete_time==None)
        return query.count()
    
    num_proposals = property(_num_proposals)


def row(instance):
    return render_tile('/instance/tiles.html', 'row', InstanceTile(instance), 
                       instance=instance, user=c.user, cached=True)
    
def header(instance, tile=None, active='issues', no_panel=False):
    if tile is None:
        tile = InstanceTile(instance)
    return render_tile('/instance/tiles.html', 'header', tile, 
                       instance=instance, active=active, no_panel=no_panel)
    