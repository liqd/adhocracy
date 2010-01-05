from datetime import datetime
import time 

from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

import adhocracy.lib.democracy as poll
from adhocracy.lib.democracy import Decision, DelegationNode
import adhocracy.model as model

class TestDelegationNode(TestController):
    
    def test_queries(self):
        motion = tt_make_motion(voting=True)
        instance = tt_get_instance()
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        
        d1to2 = model.Delegation(user1, user2, instance.root)
        model.meta.Session.add(d1to2)
        model.meta.Session.commit()
        
        dn = DelegationNode(user1, instance.root)
        assert len(dn.outbound()) == 1
             
        dn = DelegationNode(user1, motion)
        assert len(dn.outbound()) == 1
        
        dn = DelegationNode(user2, instance.root)
        assert len(dn.inbound()) == 1
        
        dn = DelegationNode(user2, motion)
        assert len(dn.inbound()) == 1
        
        d3to2 = model.Delegation(user3, user2, motion)
        model.meta.Session.add(d3to2)
        model.meta.Session.commit()
        
        dn = DelegationNode(user2, instance.root)
        assert len(dn.inbound()) == 1#
        
        dn = DelegationNode(user2, motion)
        assert len(dn.inbound()) == 2
        
        dn = DelegationNode(user2, motion)
        assert len(dn.inbound(recurse=False)) == 1
    
    def test_propagate(self):
        motion = tt_make_motion(voting=True)
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        user4 = tt_make_user()
        userA = tt_make_user()
        
        d2to1 = model.Delegation(user2, user1, motion)
        model.meta.Session.add(d2to1)
        
        dAto1 = model.Delegation(userA, user1, motion)
        model.meta.Session.add(dAto1)
        
        d3to2 = model.Delegation(user3, user2, motion)
        model.meta.Session.add(d3to2)
        
        d4to3 = model.Delegation(user4, user3, motion)
        model.meta.Session.add(d4to3)
        model.meta.Session.commit()
        
        dn = DelegationNode(user1, motion)
        assert len(dn.inbound()) == 2
        
        def inp(user, deleg, edge):
            return "foo"
        assert len(dn.propagate(inp)) == 5
    
    def test_detach(self):
        motion = tt_make_motion(voting=True)
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        
        d2to1 = model.Delegation(user2, user1, motion)
        model.meta.Session.add(d2to1)
        
        d3to1 = model.Delegation(user3, user1, motion)
        model.meta.Session.add(d3to1)
        model.meta.Session.commit()
        
        dn = DelegationNode(user1, motion)
        assert len(dn.inbound()) == 2
        
        DelegationNode.detach(user1, tt_get_instance())
        
        dn = DelegationNode(user1, motion)
        assert len(dn.inbound()) == 0
    
    def test_filter(self):
        motion = tt_make_motion(voting=True)
        instance = tt_get_instance()
        user1 = tt_make_user()
        user2 = tt_make_user()
        user3 = tt_make_user()
        
        small = model.Delegation(user1, user2, motion)
        model.meta.Session.add(small)
        
        large = model.Delegation(user1, user3, instance.root)
        model.meta.Session.add(large)
        model.meta.Session.commit()
        
        res = DelegationNode.filter_delegations([small, large])
        assert small in res
        assert large not in res
    


# TODO: delegated an isue to a user and again a motion inside that issue to the same user: make sure he only gets the right ammount of delegations
# TODO: add delegation_weight() method