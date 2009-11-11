from datetime import datetime
import time

from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

import adhocracy.lib.democracy as decision
from adhocracy.lib.democracy import Decision, Poll, DelegationNode
import adhocracy.model as model

class TestDecision(TestController):
    
    def test_direct_vcount(self):
        motion = tt_make_motion(voting=True)
        dec = Decision(motion.creator, motion)
        assert len(dec.votes) == 0
        assert len(dec.relevant_votes) == 0
        time.sleep(1)
        dec.make(model.Vote.AYE)
        #dec = Decision(motion.creator, motion)
        assert len(dec.votes) == 1
        assert len(dec.relevant_votes) == 1  
        dec.make(model.Vote.AYE)  
        assert len(dec.votes) == 2
        assert len(dec.relevant_votes) == 1
        dec2 = Decision(motion.creator, motion)
        assert len(dec2.votes) == 2
        assert len(dec2.relevant_votes) == 1
          
        
    def test_made(self):
        motion = tt_make_motion(voting=True)
        time.sleep(1)
        dec = Decision(motion.creator, motion)
        assert not dec.made()
        assert not dec.self_made()
        dec.make(model.Vote.AYE)
        time.sleep(1)
        assert dec.made()
        assert dec.self_made()        
        
    def test_delegation(self):
        motion = tt_make_motion(voting=True)
        #time.sleep(1)
        instance = tt_get_instance()
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        
        d1to2 = model.Delegation(user1, user2, instance.root)
        model.meta.Session.add(d1to2)
        model.meta.Session.commit()
        print d1to2
        Decision(user2, motion).make(model.Vote.AYE)
        time.sleep(1)
        dec = Decision(user1, motion)
        assert dec.result == model.Vote.AYE
        assert len(dec.relevant_votes) == 1   
        
        # lower scope
        d1to3 = model.Delegation(user1, user3, motion)
        model.meta.Session.add(d1to3)
        model.meta.Session.commit()
        time.sleep(1)
        Decision(user3, motion).make(model.Vote.NAY)
        time.sleep(1)
        assert len(dec.relevant_votes) == 1
        assert dec.result == model.Vote.NAY   
             
        # equal scope, same opinion
        d1to2_2 = model.Delegation(user1, user2, motion)
        model.meta.Session.add(d1to2_2)
        model.meta.Session.commit()
        #print d1to2_2
        Decision(user2, motion).make(model.Vote.NAY)
        time.sleep(1)
        dec = Decision(user1, motion)
        assert dec.result == model.Vote.NAY
        assert len(dec.relevant_votes) == 2
        
        # equal scope, different opinion
        #time.sleep(1)
        #Decision(user2, motion).make(model.Vote.AYE)
        #time.sleep(1)
        #dec = Decision(user1, motion)
        #time.sleep(1)
        #assert len(dec.relevant_votes) == 2
        #assert not dec.result
                
        # self override
        Decision(user1, motion).make(model.Vote.ABSTAIN)
        time.sleep(1)
        dec = Decision(user1, motion)
        assert dec.result == model.Vote.ABSTAIN
        assert len(dec.relevant_votes) == 1
        
    def test_delegation_override(self):
        motion = tt_make_motion(voting=True)
        time.sleep(1)
        instance = tt_get_instance()
        user1 = tt_make_user()
        user2 = tt_make_user()
        
        wide = model.Delegation(user1, user2, instance.root)
        model.meta.Session.add(wide)
        model.meta.Session.commit()
        time.sleep(1)
        Decision(user2, motion).make(model.Vote.AYE)
        time.sleep(1)
        small = model.Delegation(user1, user2, motion)
        model.meta.Session.add(small)
        model.meta.Session.commit()
        time.sleep(1)
        Decision(user2, motion).make(model.Vote.NAY)
        time.sleep(1)
        dec = Decision(user1, motion)
        
        assert len(dec.relevant_votes) == 1
        assert dec.result == model.Vote.NAY
        