from datetime import datetime
import time 

from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

from adhocracy.lib.democracy import Poll, Decision
from adhocracy.lib.democracy.result import BaseResult
import adhocracy.model as model

class TestBaseResult(TestController):
        
    def test_state(self):
        motion = tt_make_motion(voting=True)
        time.sleep(1)
        Decision(motion.creator, motion).make(model.Vote.AYE)
        Decision(tt_make_user(), motion).make(model.Vote.AYE)
        Decision(tt_make_user(), motion).make(model.Vote.AYE)
        Decision(tt_make_user(), motion).make(model.Vote.NAY)
        time.sleep(1)
        p = Poll(motion)
        r = BaseResult(p)
        
        assert r.state == model.Motion.STATE_ACTIVE
        
        Decision(tt_make_user(), motion).make(model.Vote.NAY)
        Decision(tt_make_user(), motion).make(model.Vote.NAY)
        Decision(tt_make_user(), motion).make(model.Vote.NAY)
        time.sleep(1)
        p2 = Poll(motion)
        r2 = BaseResult(p2)
        
        assert r2.state == model.Motion.STATE_VOTING
        
        