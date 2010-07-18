from util import render_tile
from datetime import datetime, timedelta

from pylons import tmpl_context as c
from webhelpers.text import truncate

from .. import democracy
from .. import helpers as h
from .. import text
from ..auth import authorization as auth
from .. import sorting
from .. import cache

from delegateable_tiles import DelegateableTile
from comment_tiles import CommentTile

class ProposalTile(DelegateableTile):
    
    def __init__(self, proposal):
        self.proposal = proposal
        self.__poll = None
        self.__decision = None
        self.__num_principals = None
        self.__comment_tile = None
        DelegateableTile.__init__(self, proposal)
    
    @property
    def tagline(self):       
        if self.proposal.comment and self.proposal.comment.latest:
            tagline = text.plain(self.proposal.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    
    @property
    def fresh(self):
        return (datetime.utcnow() - self.proposal.create_time) < timedelta(hours=36)
    
         
    @property
    def poll(self):
        if not self.__poll:
            self.__poll = self.proposal.adopt_poll
        return self.__poll
    
    
    @property
    def has_overridden(self):
        if self.decision.is_self_decided():
            return True
        return False
    
        
    @property   
    def delegates(self):
        agents = []
        if not c.user:
            return []
        for delegation in self.dnode.outbound():
            agents.append(delegation.agent)
        return set(agents)
    
    
    @property
    def num_principals(self):
        if self.__num_principals == None:
            principals = set(map(lambda d: d.principal, self.dnode.transitive_inbound()))
            if self.poll:
                principals = filter(lambda p: not democracy.Decision(p, self.poll).is_self_decided(),
                                    principals)
            self.__num_principals = len(principals)
        return self.__num_principals
    
    
    
def row(proposal):
    return render_tile('/proposal/tiles.html', 'row', ProposalTile(proposal), 
                       proposal=proposal, cached=True)  


def header(proposal, tile=None, active='goal'):
    if tile is None:
        tile = ProposalTile(proposal)
    return render_tile('/proposal/tiles.html', 'header', tile,
                       proposal=proposal, active=active)


def sidebar(proposal, tile=None):
   if tile is None:
       tile = ProposalTile(proposal)
   return render_tile('/proposal/tiles.html', 'sidebar', tile, 
                      proposal=proposal)
