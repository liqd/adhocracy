from datetime import datetime
import time 

from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

import adhocracy.model as model
from adhocracy.model import Poll

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
        time.sleep(1)
        assert not p.end_transition
        assert p.end(motion.creator)
        assert p.end_transition
        time.sleep(1)
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
        time.sleep(1)
        Decision(motion.creator, motion).make(model.Vote.AYE)
        time.sleep(1)
        assert len(motion.votes) == 1
        poll = Poll(motion)
        assert len(poll.votes) == 1
        assert len(poll.voters) == 1
        assert len(poll.decisions) == 1
        
    def test_decisions(self):
        motion = tt_make_motion(voting=True)
        Decision(motion.creator, motion).make(model.Vote.AYE)
        poll = Poll(motion)
        
    def test_vote_discard(self):
        motion = tt_make_motion(voting=True)
        time.sleep(1)
        Decision(motion.creator, motion).make(model.Vote.AYE)
        Decision(tt_make_user(), motion).make(model.Vote.AYE)
        Decision(tt_make_user(), motion).make(model.Vote.AYE)
        Decision(tt_make_user(), motion).make(model.Vote.AYE)
        time.sleep(2)
        p = Poll(motion)
        assert len(p.votes) == 4
        p.end(motion.creator)
        time.sleep(1)
        p2 = Poll.begin(motion, motion.creator)
        assert len(p2.votes) == 0
        time.sleep(1)
        Decision(motion.creator, motion).make(model.Vote.AYE)
        time.sleep(1)
        p3 = Poll(motion)
        assert len(p3.votes) == 1
        assert len(list(Poll.for_motion(motion))) == 2
        
    def test_stats(self):
        motion = tt_make_motion(voting=True)
        time.sleep(1)
        Decision(motion.creator, motion).make(model.Vote.AYE)
        time.sleep(1)
        p = Poll(motion)
        assert len(p.voters) == 1
        assert p.num_affirm == 1
        assert p.rel_for == 1.0
        Decision(tt_make_user(), motion).make(model.Vote.NAY)
        time.sleep(1)
        p = Poll(motion)
        assert len(p.voters) == 2
        assert p.num_dissent == 1
        assert p.rel_for == 1.0/2.0
        Decision(tt_make_user(), motion).make(model.Vote.ABSTAIN)
        time.sleep(1)
        p = Poll(motion)
        assert len(p.voters) == 3
        assert p.num_abstain == 1
        
    def test_average(self):
        # how to test this?? 
        avg = Poll.average_decisions(tt_get_instance())
        print "AVERAGE ", avg
        #raise ValueError
        
        
