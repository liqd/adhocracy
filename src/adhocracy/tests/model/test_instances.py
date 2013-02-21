from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestUserController(TestController):

    def test_members(self):
        from adhocracy.model import Instance, Group
        test_instance = Instance.find('test')

        members = test_instance.members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user_name, u'admin')
        voters = Group.find(u'Voter')
        tt_make_user(u'second', voters)

        members = test_instance.members()
        self.assertEqual(len(members), 2)
        self.assertEqual(sorted([member.user_name for member in
                                 test_instance.members()]),
                         ['admin', 'second'])
