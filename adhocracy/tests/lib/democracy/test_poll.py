from datetime import datetime
import time 

from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

from adhocracy.model import Poll, Vote

import adhocracy.lib.democracy as poll
from adhocracy.lib.democracy import Decision

class TestPoll(TestController):
        
    def test_nopoll(self):
        proposal = tt_make_proposal(voting=False)
        assert len(list(Poll.for_proposal(proposal))) == 0
        assert_raises(poll.NoPollException, Poll, proposal)
    
    def test_begin_end(self):
        proposal = tt_make_proposal(voting=False)
        p = Poll.begin(proposal, proposal.creator)
        assert not p.end_transition
        assert p.end(proposal.creator)
        assert p.end_transition
        assert_raises(poll.NoPollException, Poll, proposal)
    
    def test_poll(self):
        proposal = tt_make_proposal(voting=True)
        poll = Poll(proposal)
        assert poll
        assert poll.begin_transition
        assert not poll.end_transition
        assert not len(list(poll.votes))
        assert not len(poll.voters)
        assert not len(poll.decisions)
        Decision(proposal.creator, proposal).make(Vote.YES)
        assert len(proposal.votes) == 1
        poll = Poll(proposal)
        assert len(poll.votes) == 1
        assert len(poll.voters) == 1
        assert len(poll.decisions) == 1
    
    def test_decisions(self):
        proposal = tt_make_proposal(voting=True)
        Decision(proposal.creator, proposal).make(Vote.YES)
        poll = Poll(proposal)
    
    def test_stats(self):
        # REFACT: migrate to test_state - it's its own object now
        proposal = tt_make_proposal(voting=True)
        p = Poll(proposal, proposal.creator)
        Decision(proposal.creator, p).make(Vote.YES)
        state = State(proposal, p)
        assert len(state.voters) == 1
        assert p.num_affirm == 1
        assert p.rel_for == 1.0
        Decision(tt_make_user(), p).make(Vote.NO)
        p = Poll(proposal, proposal.creator)
        assert len(p.voters) == 2
        assert p.num_dissent == 1
        assert p.rel_for == 1.0/2.0
        Decision(tt_make_user(), p).make(Vote.ABSTAIN)
        p = Poll(proposal)
        assert len(p.voters) == 3
        assert p.num_abstain == 1
    
    def test_average(self):
        # how to test this?? 
        # avg = Poll.average_decisions(tt_get_instance())
        # average_decision now lives on Decision
        # print "AVERAGE ", avg
        #raise ValueError
        pass
    
# REFACT: enable the proposal to be able to have many polls in parallel