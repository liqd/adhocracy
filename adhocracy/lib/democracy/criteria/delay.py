from datetime import datetime, timedelta

from ...cache import memoize

from .. import tally as libtally
from criterion import Criterion

class DelayCriterion(Criterion):
        
    def __init__(self, state):
        super(DelayCriterion, self).__init__(state)
        self._begin_time = None
    
    def _get_delay(self):
        return timedelta(days=self.proposal.instance.activation_delay)
    
    delay = property(_get_delay)
    
    def _get_begin_time(self):
        if not self._begin_time:
            self._sfx_check_tally(self.state.tally)
        return self._begin_time
    
    begin_time = property(_get_begin_time)
    
    def _get_end_time(self):
        return self.begin_time + self.delay \
                    if self.begin_time else None
    
    end_time = property(_get_end_time) 


# REFACT: consider to remember the state from the last check and just compute what has changes since then (for StabilityCriterion and VolatilityCriterion)
class StabilityCriterion(DelayCriterion):
    """
    Check to see whether the other adoption criteria have been
    for the interval specified in the instance. 
    """
    
    def _check_criteria(self, tally):
        return self.state.majority(tally) \
            and self.state.participation(tally) \
            and self.state.alternatives(tally) 
               
    def _sfx_check_tally(self, tally):
        # sfx = side effects. 
        # Since this function has the effect of setting 
        # the begin_time classvar, it needs to be executed
        # by that property getter even if its return value 
        # has been cached on a higher level.  
        
        earliest = tally.at_time - self.delay
        tallies = self.state.get_tallies(start_at=earliest)
        # is this really necessary?
        before = libtally.at(self.poll, earliest)
        tallies.append(before) 
        
        previous_tally = None
        for t in tallies:
            # filter by time
            if t.at_time > tally.at_time:
                continue
            if t.at_time < before.at_time:
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
    
    @memoize('stability_criterion')
    def check_tally(self, tally):
        return self._sfx_check_tally(tally)
    
    def __str__(self):
        return "<StabilityCriterion(%s)>" % self.state.poll.id if self.state.poll else None


class VolatilityCriterion(DelayCriterion):
    """
    Check to see whether the adoption criteria (including stability)
    have not been met continuously for the deactivation delay time 
    span. 
    """
    
    def _check_criteria(self, tally):
        return self.state.majority(tally) \
            and self.state.participation(tally) \
            and self.state.alternatives(tally) 
    
    def _sfx_check_tally(self, tally):        
        earliest = tally.at_time - self.delay
        tallies = self.state.get_tallies(start_at=earliest)
        
        # # is this really necessary?
        # before = libtally.at(self.poll, earliest)
        # if not self._check_criteria(before):
        #     return False
        # 
        # previous_tally = None
        # for t in tallies:
        #     # filter by time
        #     if t.at_time > tally.at_time:
        #         continue
        #     if t.at_time < before.at_time:
        #         break
        #     
        #     if self._check_criteria(t):
        #         if previous_tally:
        #             self._begin_time = previous_tally.at_time
        #             return True
        #         return False
        #     
        #     previous_tally = t
        
        return False

    @memoize('volatility_criterion')
    def check_tally(self, tally):
        return self._sfx_check_tally(tally)
    
    def __str__(self):
        return "<VolatilityCriterion(%s)>" % (self.state.poll.id if self.state.poll else None)