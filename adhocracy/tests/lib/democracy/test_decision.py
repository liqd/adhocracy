from datetime import datetime
import time
from nose.tools import *

from adhocracy.model import Poll, Vote
from adhocracy.lib.democracy import Decision, DelegationNode

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
        # TODO: this quorum thing needs additional tests
    
    def test_new_decisions_are_not_decided(self):
        assert_false(self.decision.is_decided())
        assert_false(self.decision.is_self_decided())
    
    def test_can_vote_directly(self):
        self.decision.make(Vote.YES)
        assert_equals(self.decision.result, Vote.YES)
    
    def test_decision_with_a_vote_is_decided(self):
        self.decision.make(Vote.YES)
        assert_true(self.decision.is_decided())
        assert_true(self.decision.is_self_decided())
    
    def test_can_override_previous_choice(self):
        self.decision.make(Vote.YES)
        assert_equals(self.decision.result, Vote.YES)
        self.decision.make(Vote.ABSTAIN)
        assert_equals(self.decision.result, Vote.ABSTAIN)
        self.decision.make(Vote.NO)
        assert_equals(self.decision.result, Vote.NO)
    
    def test_direct_votes_always_have_only_one_relevant_vote(self):
        self.decision.make(Vote.YES)
        self.decision.make(Vote.NO)
        self.decision.make(Vote.ABSTAIN)
        assert_equals(len(self.decision.relevant_votes), 1)
    
    # History access
    
    def test_multiple_votes_for_one_decision_are_recorded_for_posterity(self):
        self.decision.make(Vote.YES)
        self.decision.make(Vote.YES)
        assert_equals(len(self.decision.votes), 2)
    
    def test_old_decisions_can_be_retrieved(self):
        self.decision.make(Vote.YES)
        self.decision.make(Vote.YES)
        self.decision.make(Vote.NO)
        # votes are FIFO
        assert_equals(self.decision.votes[0].orientation, Vote.NO)
        assert_equals(self.decision.votes[1].orientation, Vote.YES)
        assert_equals(self.decision.votes[2].orientation, Vote.YES)
    

class TestDecisionWithDelegation(TestController):
    
    def setUp(self):
        self.me = tt_make_user()
        self.high_delegate = tt_make_user()
        self.low_delegate = tt_make_user()
        
        self.motion = tt_make_motion(creator=self.me, voting=True)
        self.issue = self.motion.issue
        self.poll = Poll(self.motion, self.me)
        self.decision = Decision(self.me, self.poll)
        self.instance = tt_get_instance()
    
    def delegate(self, to, scope):
        # I would really like to say self.me.delegate_to_user_with_scope(self.high_delegate, self.instance.root)
        # However, that fails the object design criterias for now
        DelegationNode.create_delegation(from_user=self.me, to_user=to, scope=scope)
    
    def test_delegation_without_vote_is_no_vote(self):
        self.delegate(self.high_delegate, self.motion)
        self.decision.reload()
        assert_equals(len(self.decision.votes), 0)
        assert_false(self.decision.is_decided())
        assert_equals(self.decision.result, None)
    
    def test_can_do_general_delegate_to_other_user(self):
        self.delegate(self.high_delegate, self.issue)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        assert_equals(self.decision.reload().result, Vote.YES)
    
    def test_delegation_can_decide_a_decision(self):
        self.delegate(self.high_delegate, self.issue)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.decision.reload()
        assert_true(self.decision.is_decided())
    
    def test_delegated_decisions_are_not_self_decided(self):
        self.delegate(self.high_delegate, self.issue)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.decision.reload()
        assert_false(self.decision.is_self_decided())
    
    def test_issue_delegation_will_override_root_delegation(self):
        self.delegate(self.high_delegate, self.issue)
        self.delegate(self.low_delegate, self.motion.issue)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        assert_equals(self.decision.reload().result, Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.NO)
        assert_equals(self.decision.reload().result, Vote.NO)
    
    def test_motion_delegation_will_overide_issue_delegation(self):
        self.delegate(self.high_delegate, self.motion.issue)
        self.delegate(self.low_delegate, self.motion)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        assert_equals(self.decision.reload().result, Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.NO)
        assert_equals(self.decision.reload().result, Vote.NO)
    
    def test_two_delegations_at_the_same_level_that_disagree_cancel_each_other(self):
        # This is meant as a safeguard: if I don't fully trust my delegates
        # I can delegate to n delegates, and my vote will only be autocast if they all agree
        # If not, I need to decide myself
        self.delegate(self.high_delegate, self.motion)
        self.delegate(self.low_delegate, self.motion)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.NO)
        assert_equals(self.decision.reload().result, None, "needs to cast his own vote")
    
    def test_two_delegations_at_the_same_level_that_agree_reinforce_each_other(self):
        self.delegate(self.high_delegate, self.motion)
        self.delegate(self.low_delegate, self.motion)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.YES)
        assert_equals(self.decision.reload().result, Vote.YES)
    
    def test_two_delegations_at_the_same_level_are_both_relevant_votes(self):
        self.delegate(self.high_delegate, self.motion)
        self.delegate(self.low_delegate, self.motion)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        Decision(self.low_delegate, self.poll).make(Vote.YES)
        assert_equals(len(self.decision.reload().relevant_votes), 2)
    
    def test_own_vote_overrides_delegations(self):
        self.delegate(self.high_delegate, self.motion)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        self.decision.make(Vote.NO)
        assert_equals(self.decision.reload().result, Vote.NO)
    
    def test_delegation_is_recorded_as_just_another_vote(self):
        self.delegate(self.high_delegate, self.motion)
        assert_equals(len(self.decision.reload().votes), 0)
        Decision(self.high_delegate, self.poll).make(Vote.YES)
        assert_equals(len(self.decision.reload().votes), 1)
    

# TODO: can access history of delegation decisions
# TODO: test replay - this is currently in the decision - could go to the DelegationNode though
