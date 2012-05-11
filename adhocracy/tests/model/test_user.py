from adhocracy.model import Delegation, Group

from adhocracy.tests import TestController
from adhocracy.tests.testtools import (tt_get_instance, tt_make_proposal,
                                       tt_make_user)


class TestUserController(TestController):

    def test_can_delegate_via_forward_on_user(self):

        proposal = tt_make_proposal(voting=True)

        voter_group = Group.by_code(Group.CODE_VOTER)
        me = tt_make_user(instance_group=voter_group)
        delegate = tt_make_user(instance_group=voter_group)

        Delegation.create(me, delegate, proposal)
        self.assertEqual(delegate.number_of_votes_in_scope(proposal), 2)

    def test_delete_user_deletes_watches(self):
        from adhocracy.model import Watch
        voter_group = Group.by_code(Group.CODE_VOTER)
        user = tt_make_user(instance_group=voter_group)
        instance = tt_get_instance()
        watch = Watch.create(user, instance)
        self.assertFalse(watch.is_deleted())
        user.delete()
        self.assertTrue(watch.is_deleted())
