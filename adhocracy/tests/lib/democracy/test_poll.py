from datetime import datetime
import time 

from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

from adhocracy.model import Poll, Vote
from adhocracy.model.poll import NoPollException
from adhocracy.lib.democracy import Decision

class TestPoll(TestController):
        
    def test_nopoll(self):
        proposal = tt_make_proposal(voting=False)
        assert_equals(proposal.poll, None)
    
    def test_begin_end(self):
        proposal = tt_make_proposal(voting=False)
        poll = Poll(proposal, proposal.creator)
        poll.end_poll()
        assert_true(poll.has_ended())
        assert_equals(None, Poll.proposal)
    
    def test_poll(self):
        proposal = tt_make_proposal(voting=True)
        poll = proposal.poll
        assert_equals(0, len(list(poll.votes)))
        vote = proposal.creator.vote_for_proposal(proposal, Vote.YES)[0]
        assert_equals(len(poll.votes), 1)
    

# REFACT: enable the proposal to be able to have many polls in parallel