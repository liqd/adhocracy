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
        tallies = self.get_tallies(start_at=earliest)
        # is this really necessary?
        tallies.append(libtally.at(self.poll, earliest)) 
        
        previous_tally = None
        for t in tallies:
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
        
    
class StabilityCriterion(DelayCriterion):
    
    def _check_criteria(self, tally):
        return self.state.majority(tally) and \
               self.state.participation(tally)
               
    def check_tally(self, tally):
        return self._sfx_check_tally(tally)


class VolatilityCriterion(DelayCriterion):
    
    def _check_criteria(self, tally):
        return not (self.state.majority(tally) and \
               self.state.participation(tally) and \
               self.state.stability(tally))
        
    def check_tally(self, tally):
        return not self._sfx_check_tally(tally)

class ActivityCriterion(Criterion):
    
    def check_tally(self, tally):
        return self.state.stable(tally) or \
               self.state.volatile(tally)



class State(object):
    
    def __init__(self, motion, poll=None, at_time=None):
        self.motion = motion
        if not poll and len(self.motion.polls):
            for p in self.motion.polls:
                if not p.end_time:
                    poll = p
        self.poll = poll
        
        if not at_time:
            at_time = datetime.now()
        self.at_time = at_time
        
        self._tallies = []
        self._tallies_start = at_time
        
        self.majority = MajorityCriterion(self)
        self.participation = ParticipationCriterion(self)
        self.stable = StabilityCriterion(self)
        self.volatile = VolatilityCriterion(self)
        self.active = ActivityCriterion(self)
    
    polling = property(lambda self: self.poll != None)
        
    def get_tallies(self, start_at=None):
        if not self.polling:
            return []
        if not start_at:
            start_at = self.at_time - self.stable.delay
        if self._tallies_start < start_at:
            max_time = self._tallies_start 
            self._tallies += tallylib.interval(self.poll, 
                                               min_time=start_at, 
                                               max_time=self._tallies_start)
            self._tallies_start = start_at
        return self._tallies
    
    tallies = property(get_tallies)
    
    def _get_tally(self):
        tallies = self.tallies
        if not len(tallies):
            return None
        return tallies[-1]
    
    tally = property(_get_tally)
    
    def _get_poll_mutable(self):
        if not self.polling:
            return False
        return not self.stable._check_criteria(self.tally)
    
    poll_mutable = property(_get_poll_mutable)
    motion_mutable = property(lambda self: not self.polling)
            
    @classmethod
    def critical_motions(cls, instance):
        """
        Returns a list of all motions in the given ``Instance``, as a dict key with 
        a score describing the distance the ``Motion`` has towards making a state 
        change.
        
        :param instance: Instance on which to focus
        :returns: A ``dict`` of (``Motion``, score)
        """
        @memoize('motion-criticalness')
        def motion_criticalness(motion):
            state = cls(motion)
            if not state.polling:
                return None
            
            score = 1
            
            # factor 1: missing votes
            score += 1.0/float(max(1, state.participation.required - len(state.tally)))
            
            # factor 2: remaining time, i.e. urgency
            #t_remain = min(result.activation_delay, datetime.now() - result.state.begin_time)
            #score -= timedelta2seconds(t_remain)/float(timedelta2seconds(result.activation_delay))
            
            # factor 3: distance to acceptance majority
            maj_dist = abs(state.majroity.required - state.tally.rel_for)
            score *= 1 - (maj_dist/state.majority.required)
            
            return score * -1
        
        q = model.meta.Session.query(Motion).filter(Motion.instance==instance)
        scored = {}
        for motion in q.all():
            score = motion_criticalness(motion)
            if score:
                scored[motion] = score
        return scored

