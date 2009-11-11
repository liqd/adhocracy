from datetime import datetime

import adhocracy.model as model
from adhocracy.model import Motion
from ..cache import memoize

from tally import Tally


class Condition(object):
    
    def __init__(self, result):
        self.result = result
        self._met = None
        
    def _is_met(self):
        if self._met == None:
            self._met = self.check([])
        return self._met
    
    met = property(_is_met)

    
class MajorityCondition(Condition):

    def check_decisions(self, decisions):
        return Tally(decisions).rel_for > self.required_majority
    
    def check(self, decisions):
        return True
    
class ParticipationCondition(MajorityCondition):
    
    def check(self, decisions):
        return True



class StabilityCondition(MajorityCondition): 

    def check(self):
        self._stabilizing = False
        self._remaining_time = None
        now = datetime.now()
        activation_time = now - self.result.activation_delay 
        for vote in reversed(self.result.votes):
            decisions = self.result.generate_decisions(at_time=vote.create_time)
            if not self.check_tally(Tally(decisions)):
                self._remaining_time = self.result.activation_delay \
                    - (now - vote.create_time)
                break
            self._stabilizing = True
            if vote.create_time <= activation_time:
                return True
        return False
    
    def _activation_delay(self):
        return timedelta(days=self.result.motion.instance.activation_delay)
    
    activation_delay = property(_activation_delay)
        
    def _is_stabilizing(self):
        self.met
        return self._stabilizing
        
    stabilizing = property(_is_stabilizing)
    
    def _get_remaining_time(self):
        self.met
        return self._remaining_time
    
    remaining_time = property(_get_remaining_time)


ACTIVATION_CHAIN = [ParticipationCondition,
                    MajorityCondition,
                    StabilityCondition]


class ChainedCondition(Condition):
    
    def __init__(self, result, chain=ACTIVATION_CHAIN):
        super(ChainedCondition, self).__init__(result)
        self._chain = map(lambda c: c(result), chain)
        
    def __getitem__(self, condition):
        for link in self._chain:
            if type(link) == condition:
                return link
        raise IndexError()
    
    def max(self):
        return type(self._chain[-1])
    
    def check(self, decisions):
        return self.has(self.max(), decisions)
    
    def has(self, condition, decisions=None):
        decisions = decisions if decisions else self.result.decisions
        for link in self._chain:
            if not link.check(decisions):
                return False
            if type(link) == condition: # not isinstance
                return True
