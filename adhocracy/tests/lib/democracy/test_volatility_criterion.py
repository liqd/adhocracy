# REFACT: provide a package from which all of this can be ready-made imported
from datetime import timedelta

from nose.tools import assert_equals, assert_not_equals

from adhocracy.lib.democracy import State
from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_proposal, tt_make_user


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
