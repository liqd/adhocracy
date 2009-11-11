from datetime import datetime

import adhocracy.model as model
from adhocracy.model import Motion
from ..cache import memoize

import tally
from tally import Tally

class State(object):
    
    def __init__(self, result, at_time=None):
        self.result = result
        self.motion = result.motion
        self.instance = self.motion.instance 
        
        if not at_time:
            at_time = datetime.now()
        self.at_time = at_time
        
        if self.result.poll:
            self.tally = tally.at(self.result.poll, at_time)

    
    def _required_majority(self):
        """ Majority that is required for the ``Poll`` to succeed. """
        return self.instance.required_majority
    
    required_majority = property(_required_majority)

    def check_majority(self, tally):
        return tally.rel_for > self.required_majority
    
    majority = property(lambda self: self.check_majority(self.tally))
    
    def _required_participation(self):
        """ Minimal participation required for a ``Poll`` to succeed. """
        return max(1, int(self.result.average_decisions(self.motion.instance) \
                   * self.required_majority))
    
    required_participation = property(_required_participation)   
    
    def check_participation(self, tally):
        return len(tally) >= self.required_decisions
    
    participation = property(lambda self: self.check_participation(self.tally))
        
    def _activation_delay(self):
        return timedelta(days=self.instance.activation_delay)
    
    activation_delay = property(_activation_delay)
    
    def period_votes(self, at_time):
        consideration_start =  at_time - self.activation_delay
        return [v for v in self.result.votes if \
                v.create_time >= consideration_start and \
                v.create_time <= at_time]
    
    def check_activation_step(self, tally):
        # add alternatives, dependencies here 
        return self.check_majority(tally) and \
                self.check_participation(tally)
    
    def activation_begin_time(self, tally):
        last_vote = None
        for vote in reversed(self.period_votes(tally.at_time)):
            tally = self.result.tally_at(vote.create_time)
            if not self.check_activation_step(tally):
                return last_vote.create_time if last_vote else None
            last_vote = vote
        return self.consideration_start
    
    def check_activating(self, tally):
        begin_time = self.activation_begin_time(tally)
        return begin_time and begin_time != self.consideration_start  
    
    activating = property(lambda self: self.check_activating(self.at_time))
    
    def deactivation_begin_time(self, tally):
        for vote in self.period_votes(tally.at_time):
            tally = self.result.tally_at(vote.create_time)
            if not (self.check_majority(tally) and \
                self.check_participation(tally)) or \
                self.check_activating(tally):
                return vote.create_time
        return None
    
    def check_deactivating(self, tally):
        return self.deactivation_begin_time(tally)
    
    deactivating = property(lambda self: self.check_deactivating(self.tally))
    
    def _is_active(self):
        if self.majority and self.participation and \
            True: #not self.activating:
            return True
        if False: #self.deactivating:
            return True
        return False
    
    active = property(_is_active) 
