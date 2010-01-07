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
    
    def delegate(self, from_user, to_user, scope):
        return DelegationNode.create_delegation(from_user=from_user, to_user=to_user, scope=scope)
    
    
    
    def test_knows_to_whom_a_delegation_went(self):
        target = tt_make_user()
        self.delegate(self.me, target, self.proposal)
        delegations = DelegationNode(self.me, self.proposal)
        assert_equals(len(delegations.outbound()), 1)
    
    def test_can_get_direct_delegations(self):
        target = tt_make_user()
        self.delegate(self.me, target, self.proposal)
        delegations = DelegationNode(target, self.proposal)
        assert_equals(len(delegations.inbound()), 1)
    
    def test_can_get_indirect_delegations(self):
        intermediate = tt_make_user()
        target = tt_make_user()
        self.delegate(self.me, intermediate, self.proposal)
        self.delegate(intermediate, target, self.proposal)
        delegations = DelegationNode(target, self.proposal)
        assert_equals(len(delegations.inbound()), 1)
        assert_equals(len(delegations.transitive_inbound()), 2)
    
    def test_mutual_delegation_is_not_counted_as_direct_delegation(self):
        self.delegate(self.first, self.second, self.proposal)
        self.delegate(self.second, self.first, self.proposal)
        
        delegations = DelegationNode(self.first, self.proposal)
        assert_equals(len(delegations.inbound()), 1)
    
    def test_mutual_delegation_gives_two_votes_each(self):
        self.delegate(self.first, self.second, self.proposal)
        self.delegate(self.second, self.first, self.proposal)
        
        delegations = DelegationNode(self.first, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 1)
        delegations = DelegationNode(self.second, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 1)
    
    def test_delegation_is_not_used_if_user_has_voted_directly(self):
        self.delegate(self.first, self.second, self.proposal)
        self.delegate(self.second, self.first, self.proposal)
        Decision(self.first, self.proposal.poll).make(Vote.YES)
        
        delegations = DelegationNode(self.first, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 1)
        delegations = DelegationNode(self.second, self.proposal)
        assert_equals(len(delegations.transitive_inbound()), 0)
    
    def test_delegation_node_with_no_delegations_has_one_vote(self):
        node = DelegationNode(self.me, self.proposal)
        assert_equals(node.number_of_votes(), 1)
    
    def test_delegation_node_adds_direct_delegations_to_number_of_votes(self):
        self.delegate(self.first, self.me, self.proposal)
        self.delegate(self.second, self.me, self.proposal)
        node = DelegationNode(self.me, self.proposal)
        assert_equals(node.number_of_votes(), 3)
    
    def test_delegation_node_ads_indirect_delegation_to_number_of_votes(self):
        self.delegate(self.first, self.me, self.proposal)
        self.delegate(self.second, self.first, self.proposal)
        node = DelegationNode(self.me, self.proposal)
        assert_equals(node.number_of_votes(), 3)
        
    def test_if_mutual_delegation_is_broken_breaker_gets_two_votes(self):
        self.delegate(self.first, self.second, self.proposal)
        self.delegate(self.second, self.first, self.proposal)
        Decision(self.first, self.proposal.poll).make(Vote.YES)
        
        node = DelegationNode(self.first, self.proposal)
        assert_equals(node.number_of_votes(), 2)
    
    def test_if_mutual_delegation_is_broken_other_guy_just_has_his_own_vote_left(self):
        self.delegate(self.first, self.second, self.proposal)
        self.delegate(self.second, self.first, self.proposal)
        Decision(self.first, self.proposal.poll).make(Vote.YES)
        node = DelegationNode(self.first, self.proposal)
        assert_equals(node.number_of_votes(), 2)
    
    def test_can_get_delegation_count_from_user(self):
        self.delegate(self.first, self.me, self.proposal)
        assert_equals(self.me.number_of_votes_in_context(self.proposal), 2)
    
    # TODO: can reduce delegation ammount correctly
    # def test_if_mutual_delegation_is_broken_breaker_gets_two_votes(self):
    #     self.delegate(self.first, self.second, self.proposal)
    #     self.delegate(self.second, self.first, self.proposal)
    #     
    #     assert_equals()
    #     Decision(self.first, self.proposal.poll).make(Vote.YES)
    #     
    #     
    
    # TODO: direct votes always override delegations
    # This needs to be handled in inbound - not in transitive_inbound
    
    # Delegation and voting are not two methods on the same object
    # I guess thats the reason why it slipped that casting a vote actually 
    # needs to override / cancel any delegation for that user
    
    # What happens when a user wants to retract him voting so his delegations do it again for him?
    # May be hard right now as not having voted is imo not explicitly represented in the model
    
    # TODO: delegation_weight, number_of_votes
    # TODO: delegation at different levels proposals, issues, categories....
    
    # Vote ist keine Decision
    
    
    
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