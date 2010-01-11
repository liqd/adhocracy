from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

import adhocracy.model.meta as meta
import adhocracy.model as model

class TestUserController(TestController):
    
    def test_can_delegate_via_forward_on_user(self):
        proposal = tt_make_proposal(voting=True)
        me = tt_make_user()
        delegate = tt_make_user()
        
        me.delegate_to_user_in_scope(delegate, proposal)
        assert_equals(delegate.number_of_votes_in_scope(proposal), 2)
