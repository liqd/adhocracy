from datetime import datetime, timedelta

import adhocracy.model as model
from adhocracy.model import Proposal, Poll
from ..cache import memoize
from ..util import timedelta2seconds

from criteria import *

class State(object):
    
    def __init__(self, proposal, poll=None, at_time=None):
        self.proposal = proposal
        
        if at_time is None:
            at_time = datetime.utcnow()
        self.at_time = at_time
        
        if not poll and len(self.proposal.polls):
            poll = proposal.poll_at(at_time)
        self.poll = poll
                
        self._tallies = []
        
        self.majority = MajorityCriterion(self)
        self.participation = ParticipationCriterion(self)
        self.stable = StabilityCriterion(self)
        self.volatile = VolatilityCriterion(self)
        self.adopted = AdoptionCriterion(self)
        self.alternatives = AlternativesCriterion(self)
    
    polling = property(lambda self: self.poll != None)
        
    def get_tallies(self):
        if not self.polling:
            return []
        if not self._tallies:
            self._tallies = model.Tally.poll_by_interval(self.poll, self.poll.begin_time, self.at_time)
        return self._tallies
    
    tallies = property(get_tallies)
    
    def _get_tally(self):
        if not self.polling:
            return None
        return self.poll.tally
    
    tally = property(_get_tally)
    
    def _get_poll_mutable(self):
        if not self.polling:
            return False
        return not self.stable._check_criteria(self.tally)
    
    poll_mutable = property(_get_poll_mutable)
    proposal_mutable = property(lambda self: not self.polling)
