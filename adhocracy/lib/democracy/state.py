from datetime import datetime, timedelta

import adhocracy.model as model
from adhocracy.model import Proposal, Poll
from ..cache import memoize
from ..util import timedelta2seconds

import tally as libtally
from criteria import *

class State(object):
    
    def __init__(self, proposal, poll=None, at_time=None):
        self.proposal = proposal
        
        if not at_time:
            at_time = datetime.utcnow()
        self.at_time = at_time
        
        if not poll and len(self.proposal.polls):
            poll = proposal.poll_at(at_time)
        self.poll = poll
                
        self._tallies = []
        self._tallies_start = self.at_time
        
        self.majority = MajorityCriterion(self)
        self.participation = ParticipationCriterion(self)
        self.stable = StabilityCriterion(self)
        self.volatile = VolatilityCriterion(self)
        self.adopted = AdoptionCriterion(self)
        self.alternatives = AlternativesCriterion(self)
        self.dependencies = DependenciesCriterion(self)
    
    polling = property(lambda self: self.poll != None)
        
    def get_tallies(self, start_at=None):
        if not self.polling:
            return []
        if not start_at:
            start_at = self.poll.begin_time
        if self._tallies_start > start_at:
            start_at = max(start_at, self.poll.begin_time)
            self._tallies += libtally.interval(self.poll, 
                                               min_time=start_at, 
                                               max_time=self._tallies_start)
            if not len(self._tallies):
                self._tallies = [libtally.at(self.poll, start_at)]
            self._tallies_start = start_at
        return self._tallies
    
    tallies = property(get_tallies)
    
    def _get_tally(self):
        if not self.polling:
            return None
        return self.tallies[0]
    
    tally = property(_get_tally)
    
    def _get_poll_mutable(self):
        if not self.polling:
            return False
        return not self.stable._check_criteria(self.tally)
    
    poll_mutable = property(_get_poll_mutable)
    proposal_mutable = property(lambda self: not self.polling)
            
    @classmethod
    def critical_proposals(cls, instance):
        """
        Returns a list of all proposals in the given ``Instance``, as a dict key with 
        a score describing the distance the ``Proposal`` has towards making a state 
        change.
        
        :param instance: Instance on which to focus
        :returns: A ``dict`` of (``Proposal``, score)
        """
        @memoize('proposal-criticalness')
        def proposal_criticalness(proposal):
            state = State(proposal)
            if not state.polling:
                return None
            
            score = 1
            
            # factor 1: missing votes
            score += 1.0/float(max(1, state.participation.required - len(state.tally)))
            
            # factor 2: remaining time, i.e. urgency
            t_remain = min(state.stable.delay, datetime.utcnow() - \
                           state.stable.begin_time if state.stable else timedelta(seconds=0))
            score -= timedelta2seconds(t_remain)/float(timedelta2seconds(state.stable.delay))
            
            # factor 3: distance to acceptance majority
            # shitty formula
            maj_dist = max(0.000001, abs(state.majority.required - state.tally.rel_for))
            score *= 0.01/maj_dist
            
            return score * -1
        
        q = model.meta.Session.query(Proposal)
        q = q.filter(Proposal.instance==instance)
        q = q.join(Poll)
        q = q.filter(Poll.end_time==None)
        scored = {}
        for proposal in q:
            score = proposal_criticalness(proposal)
            if score:
                scored[proposal] = score
        return scored

#from beaker.util import ThreadLocal
#thread_states = ThreadLocal()
#
#def State(proposal, poll=None, at_time=None):
#    key = (proposal, poll, at_time)
#    if thread_states.get() == None:
#        thread_states.put({})
#    d = thread_states.get()
#    if d.get(key):
#        return d.get(key)
#    else:
#        s = _State(proposal, poll=None, at_time=None)
#        d[key] = s
#        thread_states.put(d)
#        return s