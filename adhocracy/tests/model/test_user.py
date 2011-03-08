from adhocracy.model import Delegation

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_proposal, tt_make_user


class TestUserController(TestController):

    def test_can_delegate_via_forward_on_user(self):

        proposal = tt_make_proposal(voting=True)
        me = tt_make_user()
        delegate = tt_make_user()

        Delegation.create(me, delegate, proposal)
        self.assertEqual(delegate.number_of_votes_in_scope(proposal), 2)
        # fixme: atm that fails cause the user does not have the
        # vote.cast permission.
