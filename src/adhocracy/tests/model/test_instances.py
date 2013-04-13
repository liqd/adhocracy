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

    def test_to_dict(self):
        from adhocracy.model import Instance
        test_instance = Instance.find('test')
        shouldbe = {'activation_delay': 7,
                    'allow_adopt': True,
                    'allow_delegate': True,
                    'allow_index': True,
                    'allow_propose': True,
                    'allow_thumbnailbadges': False,
                    'create_time': test_instance.create_time,
                    'creator': u'admin',
                    'default_group': u'voter',
                    'hidden': False,
                    'id': 1,
                    'instance_url': u'http://test.test.lan/instance/test',
                    'key': u'test',
                    'label': u'Test Instance',
                    'required_majority': 0.66,
                    'thumbnailbadges_height': None,
                    'thumbnailbadges_width': None,
                    'url': u'http://test.test.lan/instance/test'}
        result = test_instance.to_dict()
        self.assertEqual(shouldbe, result)
