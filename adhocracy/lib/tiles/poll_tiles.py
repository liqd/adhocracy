from datetime import datetime
from util import render_tile, BaseTile

from pylons import tmpl_context as c
from webhelpers.text import truncate
import adhocracy.model as model

import issue_tiles
import proposal_tiles
import comment_tiles

from .. import democracy
from .. import helpers as h
from .. import text

class PollTile(BaseTile):
    
    def __init__(self, poll):
        self.poll = poll
        self.__state = None
        self.__decision = None
        self.__dnode = None
    
    def _state(self):
        if not self.__state:
            self.__state = democracy.State(self.poll.proposal, poll=self.poll)
        return self.__state
    
    state = property(_state)
    
    def _dnode(self):
        if not self.__dnode:
            self.__dnode = democracy.DelegationNode(c.user, self.poll.scope)
        return self.__dnode
    
    dnode = property(_dnode)
    
    def _decision(self):
        if not self.__decision and c.user:
            self.__decision = democracy.Decision(c.user, self.poll)
        return self.__decision
    
    decision = property(_decision)  
        
    def _delegates(self):
        agents = []
        if not c.user:
            return []
        for delegation in self.dnode.outbound():
            agents.append(delegation.agent)
        return set(agents)
    
    delegates = property(_delegates)
    
    def delegates_result(self, result):
        agents = []
        for agent in self.delegates:
            decision = democracy.Decision(agent, self.poll)
            if decision.is_decided() and decision.result == result:
                agents.append(agent)
        return agents
    
    def _result_affirm(self):
        return round(self.poll.tally.rel_for * 100.0, 1) 
    
    result_affirm = property(_result_affirm)
    
    def _result_dissent(self):
        return round(self.poll.tally.rel_against * 100.0, 1) 
    
    result_dissent = property(_result_dissent)


def booth(poll):
    return render_tile('/poll/tiles.html', 'booth', 
                        PollTile(poll), poll=poll, 
                        user=c.user, cached=poll.has_ended()) 


def header(poll, active=''):
    if isinstance(poll.subject, model.Comment):
        return comment_tiles.header(poll.subject, active=active)
    elif isinstance(poll.scope, model.Issue):
        return issue_tiles.header(poll.scope, active=active)
    elif isinstance(poll.scope, model.Proposal):
        return proposal_tiles.header(poll.scope, active=active)
