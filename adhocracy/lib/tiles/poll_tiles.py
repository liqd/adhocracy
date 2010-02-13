from datetime import datetime
from util import render_tile, BaseTile

from pylons import tmpl_context as c
from webhelpers.text import truncate

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
    
    def _can_end_poll(self):
        if not self.poll:
            return False
        if h.has_permission('poll.abort'):
            return self.state.poll_mutable

    can_end_poll = property(_can_end_poll)
    
    def _can_vote(self):
        return (not self.poll.has_ended()) and h.has_permission('vote.cast')
    
    can_vote = property(_can_vote)
    can_delegate = can_vote
    
    def _result_affirm(self):
        return round(self.poll.tally.rel_for * 100.0, 1) 
    
    result_affirm = property(_result_affirm)
    
    def _result_dissent(self):
        return round(self.poll.tally.rel_against * 100.0, 1) 
    
    result_dissent = property(_result_dissent)
    
def booth(poll):
    return render_tile('/poll/tiles.html', 'booth', PollTile(poll), poll=poll) 