# REFACT: provide a package from which all of this can be ready-made imported
from adhocracy.tests import *
from adhocracy.tests.testtools import *
from nose.tools import *

from datetime import datetime, timedelta
import time 

from adhocracy.lib.democracy import State
from adhocracy.lib.democracy.criteria import VolatilityCriterion

import adhocracy.model as model

class TestVolatilityCriterion(TestController):
    
    def setUp(self):
        self.first = tt_make_user()
        self.second = tt_make_user()
        self.third = tt_make_user()
        self.fourth = tt_make_user()
        
        self.proposal = tt_make_proposal(voting=True)
        self.state = State(self.proposal)
        self.tally = self.state.tally
        self.criterion = self.state.volatile
    
    
    def test_can_construct_volatility_criterion(self):
        assert_not_equals(self.criterion, None)
    
    def test_default_delay_is_seven_days(self):
        assert_equals(self.criterion.delay, timedelta(days=7))
    
    def test_volatility_criterion_is_satisfied_if_no_votes_are_made(self):
        pass
        # assert_equals(self.criterion.check_tally(self.tally), True)
    

