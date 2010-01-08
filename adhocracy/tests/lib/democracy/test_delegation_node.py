from datetime import datetime
import time 

from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

import adhocracy.lib.democracy as poll
from adhocracy.lib.democracy import Decision, DelegationNode
from adhocracy.model import Delegation, Vote, Poll


import adhocracy.model as model

class TestDelegationNode(TestController):
    
    def setUp(self):
        self.me = tt_make_user()
        self.first = tt_make_user()
        self.second = tt_make_user()
        self.proposal = tt_make_proposal(voting=True)
        self.instance = tt_get_instance()
    
    def test_knows_to_whom_a_delegation_went(self):
        self.me.delegate_to_user_in_scope(self.first, self.proposal)
        delegations = DelegationNode(self.me, self.proposal)
        assert_equals(len(delegations.outbound()), 1)
    
    def test_can_get_direct_delegations(self):
        self.me.delegate_to_user_in_scope(self.first, self.proposal)
        delegations = DelegationNode(self.first, self.proposal)
        assert_equals(len(delegations.inbound()), 1)
    
    def test_can_get_indirect_delegations(self):
        self.me.delegate_to_user_in_scope(self.first, self.proposal)
        self.first.delegate_to_user_in_scope(self.second, self.proposal)
        delegations = DelegationNode(self.second, self.proposal)
        assert_equals(len(delegations.inbound()), 1)
        assert_equals(len(delegations.transitive_inbound()), 2)
    
    def test_mutual_delegation_is_not_counted_as_direct_delegation(self):
        self.first.delegate_to_user_in_scope(self.second, self.proposal)
        self.second.delegate_to_user_in_scope(self.first, self.proposal)
        
        delegations = DelegationNode(self.first, self.proposal)
        assert_equals(len(delegations.inbound()), 1)
    
    def test_mutual_delegation_gives_two_votes_each(self):
        self.first.delegate_to_user_in_scope(self.second, self.proposal)
        self.second.delegate_to_user_in_scope(self.first, self.proposal)
        
        delegations = DelegationNode(self.first, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 1)
        delegations = DelegationNode(self.second, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 1)
    
    def test_delegation_is_not_used_if_user_has_voted_directly(self):
        self.first.delegate_to_user_in_scope(self.second, self.proposal)
        self.second.delegate_to_user_in_scope(self.first, self.proposal)
        Decision(self.first, self.proposal.poll).make(Vote.YES)
        
        delegations = DelegationNode(self.first, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 1)
        delegations = DelegationNode(self.second, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 0)
    
    def test_delegation_node_with_no_delegations_has_one_vote(self):
        node = DelegationNode(self.me, self.proposal)
        assert_equals(node.number_of_votes(), 1)
    
    def test_delegation_node_adds_direct_delegations_to_number_of_votes(self):
        self.first.delegate_to_user_in_scope(self.me, self.proposal)
        self.second.delegate_to_user_in_scope(self.me, self.proposal)
        node = DelegationNode(self.me, self.proposal)
        assert_equals(node.number_of_votes(), 3)
    
    def test_delegation_node_ads_indirect_delegation_to_number_of_votes(self):
        self.first.delegate_to_user_in_scope(self.me, self.proposal)
        self.second.delegate_to_user_in_scope(self.first, self.proposal)
        node = DelegationNode(self.me, self.proposal)
        assert_equals(node.number_of_votes(), 3)
        
    def test_if_mutual_delegation_is_broken_breaker_gets_two_votes(self):
        self.first.delegate_to_user_in_scope(self.second, self.proposal)
        self.second.delegate_to_user_in_scope(self.first, self.proposal)
        Decision(self.first, self.proposal.poll).make(Vote.YES)
        
        node = DelegationNode(self.first, self.proposal)
        assert_equals(node.number_of_votes(), 2)
    
    def test_if_mutual_delegation_is_broken_other_guy_just_has_his_own_vote_left(self):
        self.first.delegate_to_user_in_scope(self.second, self.proposal)
        self.second.delegate_to_user_in_scope(self.first, self.proposal)
        Decision(self.first, self.proposal.poll).make(Vote.YES)
        node = DelegationNode(self.first, self.proposal)
        assert_equals(node.number_of_votes(), 2)
    
    def test_if_proposal_has_no_poll_no_direct_vote_overides_delegations(self):
        proposal_without_poll = tt_make_proposal()
        self.first.delegate_to_user_in_scope(self.second, proposal_without_poll)
        node = DelegationNode(self.second, proposal_without_poll)
        assert_equals(node.number_of_votes(), 2)

class TestInteractionOfDelegationOnDifferentLevels(TestController):
    
    def setUp(self):
        self.me = tt_make_user()
        self.first = tt_make_user()
        self.second = tt_make_user()
        self.proposal = tt_make_proposal(voting=True)
    
    def test_direct_delegations_on_different_levels_add_to_each_other(self):
        self.first.delegate_to_user_in_scope(self.me, self.proposal.issue)
        self.second.delegate_to_user_in_scope(self.me, self.proposal)
        assert_equals(self.me.number_of_votes_in_scope(self.proposal), 3)
    
    def test_direct_delegations_on_different_levels_can_overide_each_other(self):
        self.me.delegate_to_user_in_scope(self.first, self.proposal.issue)
        self.me.delegate_to_user_in_scope(self.second, self.proposal)
        assert_equals(self.first.number_of_votes_in_scope(self.proposal), 1)
    
    def test_user_with_two_delegations_gets_counted_for_each_delegator_as_number_of_votes(self):
        self.me.delegate_to_user_in_scope(self.first, self.proposal)
        self.me.delegate_to_user_in_scope(self.second, self.proposal)
        
        node = self.first.delegation_node(self.proposal)
        assert_equals(len(node.inbound()), 1)
        # assert_equals(len(node.transitive_inbound()), 0)
        
        assert_equals(self.first.number_of_votes_in_scope(self.proposal), 2)
        assert_equals(self.second.number_of_votes_in_scope(self.proposal), 2)
    
    # TODO: user has two outgoing delegations on one level
    # who gets how much votes? everybody gets the vote
    # but in an actual poll this needs to be prevented


    
    def test_queries(self):
        proposal = tt_make_proposal(voting=True)
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        
        d1to2 = model.Delegation(user1, user2, proposal.issue)
        model.meta.Session.add(d1to2)
        model.meta.Session.commit()
        
        dn = DelegationNode(user1, proposal.issue)
        assert len(dn.outbound()) == 1
             
        dn = DelegationNode(user1, proposal)
        assert len(dn.outbound()) == 1
        
        dn = DelegationNode(user2, proposal.issue)
        assert len(dn.inbound()) == 1
        
        dn = DelegationNode(user2, proposal)
        assert len(dn.inbound()) == 1
        
        d3to2 = model.Delegation(user3, user2, proposal)
        model.meta.Session.add(d3to2)
        model.meta.Session.commit()
        
        dn = DelegationNode(user2, proposal.issue)
        assert len(dn.inbound()) == 1#
        
        dn = DelegationNode(user2, proposal)
        assert len(dn.inbound()) == 2
        
        dn = DelegationNode(user2, proposal)
        assert len(dn.inbound(recurse=False)) == 1
    
    def test_propagate(self):
        proposal = tt_make_proposal(voting=True)
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        user4 = tt_make_user()
        userA = tt_make_user()
        
        d2to1 = model.Delegation(user2, user1, proposal)
        model.meta.Session.add(d2to1)
        
        dAto1 = model.Delegation(userA, user1, proposal)
        model.meta.Session.add(dAto1)
        
        d3to2 = model.Delegation(user3, user2, proposal)
        model.meta.Session.add(d3to2)
        
        d4to3 = model.Delegation(user4, user3, proposal)
        model.meta.Session.add(d4to3)
        model.meta.Session.commit()
        
        dn = DelegationNode(user1, proposal)
        assert len(dn.inbound()) == 2
        
        def inp(user, deleg, edge):
            return "foo"
        assert len(dn.propagate(inp)) == 5
    
    def test_detach(self):
        proposal = tt_make_proposal(voting=True)
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        
        d2to1 = model.Delegation(user2, user1, proposal)
        model.meta.Session.add(d2to1)
        
        d3to1 = model.Delegation(user3, user1, proposal)
        model.meta.Session.add(d3to1)
        model.meta.Session.commit()
        
        dn = DelegationNode(user1, proposal)
        assert len(dn.inbound()) == 2
        
        DelegationNode.detach(user1, tt_get_instance())
        
        dn = DelegationNode(user1, proposal)
        assert len(dn.inbound()) == 0
    
    def test_filter(self):
        proposal = tt_make_proposal(voting=True)
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        
        small = model.Delegation(user1, user2, proposal)
        model.meta.Session.add(small)
        
        large = model.Delegation(user1, user3, proposal.issue)
        model.meta.Session.add(large)
        model.meta.Session.commit()
        
        res = DelegationNode.filter_delegations([small, large])
        assert small in res
        assert large not in res
    


# TODO: delegated an isue to a user and again a proposal inside that issue to the same user: make sure he only gets the right ammount of delegations
# TODO: add delegation_weight() method
# TODO: circular delegation should be handled correctly

# What I'd like to have as an api would be:
# first.vote(self.proposal).yes()
# TODO: when delegating to multiple people, how much weight do they get to give when they delegate? Hopefully not each +1...
# TODO: how is the split delegation handled across multiple levels? I think they just override each other
# when delegating on different levels, the delegation wheight of each delegation-target depends on the context...

# Delegation and voting are not two methods on the same object
# I guess thats the reason why it slipped that casting a vote actually 
# needs to override / cancel any delegation for that user

# What happens when a user wants to retract him voting so his delegations do it again for him?
# May be hard right now as not having voted is imo not explicitly represented in the model

