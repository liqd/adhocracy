from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestUserController(TestController):

    def _make_one(self):
        from adhocracy.model import Badge, UserBadge

        creator = tt_make_user('creator')
        badged_user = tt_make_user('badged_user')
        badge = Badge.create('testbadge', '#ccc', 'description')
        UserBadge.create(badged_user, badge, creator)
        return creator, badged_user, badge

    def test_userbadges_created(self):
        from adhocracy.model import Badge, meta
        # the created badge
        creator, badged_user, badge = self._make_one()
        self.assertEqual(meta.Session.query(Badge).count(), 1)
        queried_badge = meta.Session.query(Badge).first()
        self.assertTrue(badge is queried_badge)
        self.assertEqual(queried_badge.title, 'testbadge')

        # references on the badged user
        self.assertEqual(badged_user.badges, [badge])
        self.assertEqual(badged_user.badges[0].users, [badged_user])
        return badge, badged_user

    def test_remove_badge_from_user(self):
        from adhocracy.model import meta, UserBadge
        creator, badged_user, badge = self._make_one()
        self.assertEqual(badged_user.badges, [badge])
        badged_user.badges.remove(badge)
        self.assertEqual(badged_user.badges, [])
        self.assertEqual(badge.users, [])
        self.assertEqual(meta.Session.query(UserBadge).count(), 0)

    def test_remove_user_from_badge(self):
        from adhocracy.model import meta, UserBadge
        creator, badged_user, badge = self._make_one()
        self.assertEqual(badge.users, [badged_user])
        badge.users.remove(badged_user)
        self.assertEqual(badge.users, [])
        self.assertEqual(badged_user.badges, [])
        self.assertEqual(meta.Session.query(UserBadge).count(), 0)

    def test_to_dict(self):
        creator, badged_user, badge = self._make_one()
        result = badge.to_dict()
        self.assertEqual(result, {'color': '#ccc', 'title': 'testbadge',
                                  'id': 1, 'users': [u'badged_user'],
                                  'display_group': False, 'group': None})
