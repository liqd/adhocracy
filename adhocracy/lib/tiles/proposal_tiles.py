from util import render_tile

from pylons import tmpl_context as c
from webhelpers.text import truncate

from .. import democracy
from .. import helpers as h
from .. import text
from .. import authorization as auth
from .. import sorting
from .. import karma

from delegateable_tiles import DelegateableTile
from comment_tiles import CommentTile

class ProposalTile(DelegateableTile):
    
    def __init__(self, proposal):
        self.proposal = proposal
        self.__poll = None
        self.__state = None
        self.__decision = None
        self.__num_principals = None
        self.__comment_tile = None
        DelegateableTile.__init__(self, proposal)
    
    def _tagline(self):       
        if self.proposal.comment and self.proposal.comment.latest:
            tagline = text.plain(self.proposal.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    def _poll(self):
        if not self.__poll:
            self.__poll = self.proposal.adopt_poll
        return self.__poll
    
    poll = property(_poll)
    
    def _state(self):
        if not self.__state:
            self.__state = democracy.State(self.proposal, poll=self.poll)
        return self.__state
    
    state = property(_state)    
    
            
    def _can_edit(self):
        return h.has_permission('proposal.edit') \
                and not self.is_immutable
    
    can_edit = property(_can_edit)    
    
    def _can_delete(self):
        return h.has_permission('proposal.delete') \
                and not self.is_immutable
    
    can_delete = property(_can_delete)
    
    def _has_overridden(self):
        if self.decision.is_self_decided():
            return True
        return False
    
    def _can_create_canonical(self):
        return h.has_permission('comment.create') \
                and not self.is_immutable
    
    can_create_canonical = property(_can_create_canonical)
    
    def _has_canonicals(self):
        return len(self.proposal.canonicals) > 0
    
    has_canonicals = property(_has_canonicals)
    
    def _can_begin_poll(self):
        if not self.has_canonicals:
            return False
        if self.poll:
            return False
        return h.has_permission('poll.create')
    
    can_begin_poll = property(_can_begin_poll)
        
    def _is_immutable(self):
        return not self.proposal.is_mutable()
    
    is_immutable = property(_is_immutable)
    
    def _delegates(self):
        agents = []
        if not c.user:
            return []
        for delegation in self.dnode.outbound():
            agents.append(delegation.agent)
        return set(agents)
    
    delegates = property(_delegates)
    
    def _num_principals(self):
        if self.__num_principals == None:
            principals = set(map(lambda d: d.principal, self.dnode.transitive_inbound()))
            if self.poll:
                principals = filter(lambda p: not democracy.Decision(p, self.poll).is_self_decided(),
                                    principals)
            self.__num_principals = len(principals)
        return self.__num_principals
    
    num_principals = property(_num_principals)
    
    def _comment_tile(self):
        if not self.__comment_tile:
            self.__comment_tile = CommentTile(self.proposal.comment)
        return self.__comment_tile
    
    comment_tile = property(_comment_tile)
    
    def _support(self):
        return karma.comment_score(self.proposal.comment, recurse=False)
    
    support = property(_support)

    def _position(self):
        if not c.user:
            return 0
        return karma.position(c.user, self.proposal.comment)
    
    position = property(_position)

def row(proposal):
    return render_tile('/proposal/tiles.html', 'row', ProposalTile(proposal), 
                       proposal=proposal, cached=True)  

def header(proposal, tile=None, active='goal'):
    if tile is None:
        tile = ProposalTile(proposal)
    return render_tile('/proposal/tiles.html', 'header', tile, 
                       proposal=proposal, active=active)
