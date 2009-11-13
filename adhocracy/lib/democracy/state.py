from datetime import datetime, timedelta

import adhocracy.model as model
from adhocracy.model import Motion, Poll
from ..cache import memoize
from ..util import timedelta2seconds

import tally as libtally
from criteria import *

class State(object):
    
    def __init__(self, motion, poll=None, at_time=None):
        self.motion = motion
        
        if not at_time:
            at_time = datetime.now()
        self.at_time = at_time
        
        if not poll and len(self.motion.polls):
            poll = motion.poll_at(at_time)
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
            start_at = self.at_time - self.stable.delay
        if self._tallies_start > start_at:
            start_at = max(start_at, self.poll.begin_time)
            #print "START AT ", start_at
            self._tallies += libtally.interval(self.poll, 
                                               min_time=start_at, 
                                               max_time=self._tallies_start)
            if not len(self._tallies):
                self._tallies = [libtally.at(self.poll, start_at)]
            #print "TALLIES ", self._tallies
            self._tallies_start = start_at
        return self._tallies
    
    tallies = property(get_tallies)
    
    def _get_tally(self):
        if not self.polling:
            return []
        return self.tallies[0]
    
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
            state = State(motion)
            if not state.polling:
                print "MOTION HAS NO POLL"
                return None
            
            score = 1
            
            # factor 1: missing votes
            score += 1.0/float(max(1, state.participation.required - len(state.tally)))
            
            # factor 2: remaining time, i.e. urgency
            t_remain = min(state.stable.delay, datetime.now() - \
                           state.stable.begin_time if state.stable else timedelta(seconds=0))
            score -= timedelta2seconds(t_remain)/float(timedelta2seconds(state.stable.delay))
            
            # factor 3: distance to acceptance majority
            # shitty formula
            maj_dist = max(0.000001, abs(state.majority.required - state.tally.rel_for))
            score *= 0.01/maj_dist
            
            return score * -1
        
        q = model.meta.Session.query(Motion)
        q = q.filter(Motion.instance==instance)
        q = q.join(Poll)
        q = q.filter(Poll.end_time==None)
        scored = {}
        for motion in q:
            score = motion_criticalness(motion)
            if score:
                scored[motion] = score
        return scored

