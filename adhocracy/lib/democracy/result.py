from datetime import datetime, timedelta

import adhocracy.model as model
from adhocracy.model import Motion, Poll
from ..cache import memoize

from decision import Decision
import tally
from tally import Tally
from state import State

class Result(object):
    
    def __init__(self, motion, poll=None):
        self.motion = motion
        if not poll and len(self.motion.polls):
            for p in self.motion.polls:
                if not p.end_time:
                    poll = p
        self.poll = poll
        self.state = State(self)
        if self.poll:
            #self.tally = tally.at(poll, poll.votes[0].create_time)
            tallies = tally.interval(poll, datetime.now() - timedelta(hours=1), datetime.now())
            self.tally = tallies[-1]
            #print "TALLIES", tallies
            #print "TALLY ", self.tally
    
    polling = property(lambda self: self.poll != None)
    
    def _can_cancel(self):
        print "CAN CANCEL: NOT DONE"
        return True
    
    can_cancel = property(_can_cancel)
    
    def __repr__(self):
        return "<Result(%s)>" % self.poll

    
    @classmethod
    def average_decisions(cls, instance):
        """
        The average number of decisions that a ``Poll`` in the given instance 
        has. For each motion, this only includes the current poll in order to 
        not accumulate too much historic data.
        
        :param instance: the ``Instance`` for which to calculate the average.   
        """
        @memoize('average_decisions', 84600)
        def avg_decisions(instance):
            query = model.meta.Session.query(Poll)
            query = query.join(Motion).filter(Motion.instance_id==instance.id)
            query = query.filter(Poll.end_time==None)
            decisions = []
            for poll in query:
                result = Result(poll.motion, poll=poll)
                if result.is_polling:
                    poll_decisions = len(result.decisions)
                    if decisions:
                        decisions.append(poll_decisions)
            return sum(decisions)/float(max(1,len(decisions)))
        return avg_decisions(instance)

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
            result = cls(motion)
            if not result.poll:
                return None
            
            score = 1
            
            # factor 1: missing votes
            score += 1.0/float(max(1, result.required_decisions - len(result.decisions)))
            
            # factor 2: remaining time, i.e. urgency
            #t_remain = min(result.activation_delay, datetime.now() - result.state.begin_time)
            #score -= timedelta2seconds(t_remain)/float(timedelta2seconds(result.activation_delay))
            
            # factor 3: distance to acceptance majority
            maj_dist = abs(result.required_majority - result.rel_for)
            score *= 1 - (maj_dist/result.required_majority)
            
            return score * -1
        
        q = model.meta.Session.query(Motion).filter(Motion.instance==instance)
        scored = {}
        for motion in q.all():
            score = motion_criticalness(motion)
            if score:
                scored[motion] = score
        return scored

