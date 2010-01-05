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
        motion = tt_make_motion(voting=False)
        assert len(list(Poll.for_motion(motion))) == 0
        assert_raises(poll.NoPollException, Poll, motion)
    
    def test_begin_end(self):
        motion = tt_make_motion(voting=False)
        p = Poll.begin(motion, motion.creator)
        assert not p.end_transition
        assert p.end(motion.creator)
        assert p.end_transition
        assert_raises(poll.NoPollException, Poll, motion)
    
    def test_poll(self):
        motion = tt_make_motion(voting=True)
        poll = Poll(motion)
        assert poll
        assert poll.begin_transition
        assert not poll.end_transition
        assert not len(list(poll.votes))
        assert not len(poll.voters)
        assert not len(poll.decisions)
        Decision(motion.creator, motion).make(Vote.YES)
        assert len(motion.votes) == 1
        poll = Poll(motion)
        assert len(poll.votes) == 1
        assert len(poll.voters) == 1
        assert len(poll.decisions) == 1
    
    def test_decisions(self):
        motion = tt_make_motion(voting=True)
        Decision(motion.creator, motion).make(Vote.YES)
        poll = Poll(motion)
    
    def test_stats(self):
        # REFACT: migrate to test_state - it's its own object now
        motion = tt_make_motion(voting=True)
        p = Poll(motion, motion.creator)
        Decision(motion.creator, p).make(Vote.YES)
        state = State(motion, p)
        assert len(state.voters) == 1
        assert p.num_affirm == 1
        assert p.rel_for == 1.0
        Decision(tt_make_user(), p).make(Vote.NO)
        p = Poll(motion, motion.creator)
        assert len(p.voters) == 2
        assert p.num_dissent == 1
        assert p.rel_for == 1.0/2.0
        Decision(tt_make_user(), p).make(Vote.ABSTAIN)
        p = Poll(motion)
        assert len(p.voters) == 3
        assert p.num_abstain == 1
    
    def test_average(self):
        # how to test this?? 
        # avg = Poll.average_decisions(tt_get_instance())
        # average_decision now lives on Decision
        # print "AVERAGE ", avg
        #raise ValueError
        pass
    
# REFACT: enable the motion to be able to have many polls in parallel