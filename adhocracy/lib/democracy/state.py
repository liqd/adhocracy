from datetime import datetime

import adhocracy.model as model
from adhocracy.model import Motion
from ..cache import memoize

import tally as libtally
from tally import Tally
from decision import Decision

class Criterion(object):
    
    def __init__(self, state):
        self.state = state
        self.motion = state.motion
        self.poll = state.poll
        self._checked = None
        
    def check(self):
        if self._checked == None:
            self._checked = self.check_tally(self.state.tally)
        return self._checked
    
    def check_tally(self, tally):
        raise NotImplemented()
    
    def __nonzero__(self):
        return self.check()
    
    def __call__(self, tally):
        return self.check_tally(tally)
    
    def __repr__(self):
        return "<Criterion(%s,%s)>" % (self.motion.id, self.poll.id)
    
    def __str__(self): 
        # relevant for cache keys
        return repr(self)


class ParticipationCriterion(Criterion):
    
    def _get_required(self):
        return max(1, int(Decision.average_decisions(self.motion.instance) \
                   * self.motion.instance.required_majority))
    
    required = property(_get_required)
    
    def check_tally(self, tally):
        return len(tally) >= self.required
    
    
class MajorityCriterion(Criterion):
    
    def _get_required(self):
        return self.motion.instance.required_majority
    
    required = property(_get_required)
    
    def check_tally(self, tally):
        return tally.rel_for > self.required

class DelayCriterion(Criterion):
        
    def __init__(self, state):
        super(DelayCriterion, self).__init__(state)
        self._begin_time = None
    
    def _get_delay(self):
        return timedelta(days=self.motion.instance.activation_delay)
    
    delay = property(_get_delay)
    
    def _get_begin_time(self):
        if not self._begin_time:
            self._sfx_check_tally(self.state.tally)
        return self._begin_time
    
    begin_time = property(_get_begin_time)
    
    def _get_end_time(self):
        return self.begin_time + self.delay \
                    if begin_time else None
    
    end_time = property(_get_end_time)
        
    def _sfx_check_tally(self, tally):
        # sfx = side effects. 
        # Since this function has the effect of setting 
        # the begin_time classvar, it needs to be executed
        # by that property getter even if its return value 
        # has been cached on a higher level.  
        
        earliest = tally.at_time - self.delay
        
        # is this really necessary?
        before = libtally.at(self.poll, earliest)
        
        previous_tally = None
        for t in self.state.tallies + [before]:
            # filter by time
            if t.at_time > tally.at_time:
                continue
            if t.at_time < earliest:
                break
        
            if not self._check_criteria(t):
                if previous_tally:
                    self._begin_time = previous_tally.at_time
                return False
            
            previous_tally = t
        
        if previous_tally:
            self._begin_time = earliest
            return True
        return False    
        
    
class StabilityCriterion(Criterion):
    
    def _check_criteria(self, tally):
        return self.state.majority(tally) and \
               self.state.participation(tally)
               
    def check_tally(self, tally):
        return self._sfx_check_tally(tally)


class VolatilityCriterion(Criterion):
    
    def _check_criteria(self, tally):
        return not (self.state.majority(tally) and \
               self.state.participation(tally) and \
               self.state.stability(tally))
        
    def check_tally(self, tally):
        return not self._sfx_check_tally(tally)




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


    def _require_tallies(self, min_time, max_time):
        pass








    
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
