from datetime import datetime
import time
from nose.tools import *

from adhocracy.model import Poll
from adhocracy.lib.democracy import Decision, DelegationNode
import adhocracy.model as model

from adhocracy.tests import *
from adhocracy.tests.testtools import *


class TestDecisionWithoutDelegation(TestController):
    
    def setUp(self):
        self.motion = tt_make_motion(voting=True)
        self.poll = Poll(self.motion, self.motion.creator)
        self.decision = Decision(self.motion.creator, self.poll)
    
    def test_new_decisions_have_no_votes(self):
        assert_equals(len(self.decision.votes), 0)
        assert_equals(len(self.decision.relevant_votes), 0)
        assert_equals(self.decision.result, None, "Not voted yet == not recorded for quorum")
    
    def test_new_decisions_are_not_decided(self):
        assert_false(self.decision.is_decided())
        assert_false(self.decision.is_self_decided())
    
    def test_can_vote_directly(self):
        self.decision.make(model.Vote.AYE)
        assert_equals(self.decision.result, model.Vote.AYE)
    
    def test_decision_with_a_vote_is_decided(self):
        self.decision.make(model.Vote.AYE)
        assert_true(self.decision.is_decided())
        assert_true(self.decision.is_self_decided())
    
    def test_can_override_previous_choice(self):
        self.decision.make(model.Vote.AYE)
        assert_equals(self.decision.result, model.Vote.AYE)
        self.decision.make(model.Vote.ABSTAIN)
        assert_equals(self.decision.result, model.Vote.ABSTAIN)
        self.decision.make(model.Vote.NAY)
        assert_equals(self.decision.result, model.Vote.NAY)
    
    def test_direct_votes_always_have_only_one_relevant_vote(self):
        self.decision.make(model.Vote.AYE)
        self.decision.make(model.Vote.NAY)
        self.decision.make(model.Vote.ABSTAIN)
        assert_equals(len(self.decision.relevant_votes), 1)
    
    # History access
    
    def test_multiple_votes_for_one_decision_are_recorded_for_posterity(self):
        self.decision.make(model.Vote.AYE)
        self.decision.make(model.Vote.AYE)
        assert_equals(len(self.decision.votes), 2)
    
    def test_old_decisions_can_be_retrieved(self):
        self.decision.make(model.Vote.AYE)
        self.decision.make(model.Vote.NAY)
        self.decision.make(model.Vote.AYE)
        assert_equals(self.decision.votes[0].orientation, model.Vote.AYE)
        assert_equals(self.decision.votes[1].orientation, model.Vote.NAY)
        assert_equals(self.decision.votes[2].orientation, model.Vote.AYE)
    

class TestDecisionWithDelegation(TestController):
    
    def setUp(self):
        self.motion = tt_make_motion(voting=True)
        self.poll = Poll(self.motion, self.motion.creator)
        self.decision = Decision(self.motion.creator, self.poll)
        self.instance = tt_get_instance()
        self.user1 = tt_make_user()
        self.user2 = tt_make_user()
    
    def test_can_delegate_to_other_user(self):
        # TODO: works - but is not pretty
        # consider a method on DelegationNode 
        delegation = model.Delegation(self.user1, self.user2, self.instance.root)
        model.meta.Session.add(delegation)
        model.meta.Session.commit()
        
        Decision(self.user2, self.poll).make(model.Vote.AYE)
        decision = Decision(self.user1, self.poll)
        assert_equals(decision.result, model.Vote.AYE)
        assert_equals(len(decision.relevant_votes), 1)
    
    # TODO: test that delegations on different scopes interact correctly
    # def test_delegation(self):
    #     #time.sleep(1)
    #     instance = tt_get_instance()
    #     user1 = tt_make_user()
    #     user2 = tt_make_user()
    #     user3 = tt_make_user()
    #     
    #     d1to2 = model.Delegation(user1, user2, instance.root)
    #     model.meta.Session.add(d1to2)
    #     model.meta.Session.commit()
    #     print d1to2
    #     Decision(user2, motion).make(model.Vote.AYE)
    #     dec = Decision(user1, motion)
    #     assert dec.result == model.Vote.AYE
    #     assert len(dec.relevant_votes) == 1   
    #     
    #     # lower scope
    #     d1to3 = model.Delegation(user1, user3, motion)
    #     model.meta.Session.add(d1to3)
    #     model.meta.Session.commit()
    #     Decision(user3, motion).make(model.Vote.NAY)
    #     assert len(dec.relevant_votes) == 1
    #     assert dec.result == model.Vote.NAY   
    #          
    #     # equal scope, same opinion
    #     d1to2_2 = model.Delegation(user1, user2, motion)
    #     model.meta.Session.add(d1to2_2)
    #     model.meta.Session.commit()
    #     #print d1to2_2
    #     Decision(user2, motion).make(model.Vote.NAY)
    #     dec = Decision(user1, motion)
    #     assert dec.result == model.Vote.NAY
    #     assert len(dec.relevant_votes) == 2
        
        # equal scope, different opinion
        #time.sleep(1)
        #Decision(user2, motion).make(model.Vote.AYE)
        #time.sleep(1)
        #dec = Decision(user1, motion)
        #time.sleep(1)
        #assert len(dec.relevant_votes) == 2
        #assert not dec.result
                
        # self override
        # Decision(user1, motion).make(model.Vote.ABSTAIN)
        # dec = Decision(user1, motion)
        # assert dec.result == model.Vote.ABSTAIN
        # assert len(dec.relevant_votes) == 1
        
    # TODO test that a user can override their delegate
    #  this should include proper chain interruption
    #  i.e. A->B->C, B votes self after A voted, C will now have to adopt B's opinion. 
    # def test_delegation_override(self):
    #     motion = tt_make_motion(voting=True)
    #     instance = tt_get_instance()
    #     user1 = tt_make_user()
    #     user2 = tt_make_user()
    #     
    #     wide = model.Delegation(user1, user2, instance.root)
    #     model.meta.Session.add(wide)
    #     model.meta.Session.commit()
    #     Decision(user2, motion).make(model.Vote.AYE)
    #     small = model.Delegation(user1, user2, motion)
    #     model.meta.Session.add(small)
    #     model.meta.Session.commit()
    #     Decision(user2, motion).make(model.Vote.NAY)
    #     dec = Decision(user1, motion)
    #     
    #     assert len(dec.relevant_votes) == 1
    #     assert dec.result == model.Vote.NAY
    # 
    # # This tests a weird bit of the replay mechanism - not sure what that is or if we need it
    # def test_can_make_two_two_decisions_for_one_poll(self):
    #     self.decision.make(model.Vote.AYE)
    #     decision2 = Decision(self.motion.creator, self.poll)
    #     decision2.make(model.Vote.AYE)
    #     assert_equals(len(decision2.votes), 2)
    #     assert_equals(len(decision2.relevant_votes), 1)
    

# TODO: special case: two delegations with different votes should cancel
# TODO: delegated case can be decided by the delegator or by the user itself
