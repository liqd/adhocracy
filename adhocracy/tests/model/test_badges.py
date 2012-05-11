# coding=utf-8
from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestBadgeController(TestController):

    def test_cannot_add_base_Badge(self):
        """
        We cannot add the base `Badge` to the database cause
        It has no polymorphic_identity and is only ment as
        a base class even if it's mapped. Kindof a reminder.
        """
        from sqlalchemy.exc import IntegrityError
        from adhocracy.model import Badge
        #add badge
        self.assertRaises(IntegrityError, Badge.create, u'badge ü',
                          u'#ccc', u'description ü')

    def test_to_dict(self):
        from adhocracy.model import CategoryBadge, Instance
        instance = Instance.find('test')
        badge = CategoryBadge.create(u'badge', u'#ccc', u'description',
                                     instance=instance)
        result = badge.to_dict()
        result = sorted(result.items())
        expected = {'title': u'badge',
                    'color': u'#ccc',
                    'description': u'description',
                    'id': 1,
                    'instance': instance.id}
        expected = sorted(expected.items())
        self.assertEqual(result, expected)

    def test_get_all_badgets(self):
        #setup
        from adhocracy.model import Badge, CategoryBadge, DelegateableBadge
        from adhocracy.model import UserBadge, Instance
        instance = Instance.find(u'test')
        # create Badges, for each type a global and an instance badge
        UserBadge.create(u'badge ü', u'#ccc', u'description ü')
        UserBadge.create(u'ü', u'#ccc', u'ü', instance=instance)
        DelegateableBadge.create(u'badge ü', u'#ccc', u'description ü')
        DelegateableBadge.create(u'badge ü', u'#ccc', u'description ü',
                                 instance=instance)
        CategoryBadge.create(u'badge ü', u'#ccc', u"desc")
        CategoryBadge.create(u'badge ü', u'#ccc', u"desc", instance=instance)

        # all delegateable badges
        self.assert_(len(DelegateableBadge.all()) == 1)
        self.assert_(len(DelegateableBadge.all(instance=instance)) == 1)
        # all delegateable category badges
        self.assert_(len(CategoryBadge.all()) == 1)
        self.assert_(len(CategoryBadge.all(instance=instance)) == 1)
        # all user badgets
        self.assert_(len(UserBadge.all()) == 1)
        self.assert_(len(UserBadge.all(instance=instance)) == 1)
        # We can get all Badges by using `Badge`
        self.assert_(len(Badge.all()) == 3)
        self.assert_(len(Badge.all(instance=instance)) == 3)

        self.assert_(len(Badge.all_q().all()) == 6)


class TestUserController(TestController):

    def _make_one(self):
        """Returns creator, badged user and badge"""

        from adhocracy import model
        creator = tt_make_user('creator')
        badged_user = tt_make_user('badged_user')
        badge = model.UserBadge.create(u'testbadge', u'#ccc', u'description')
        badge.assign(badged_user, creator)
        return creator, badged_user, badge

    def test_userbadges_created(self):
        from adhocracy.model import Badge, meta
        # the created badge
        creator, badged_user, badge = self._make_one()
        queried_badge = meta.Session.query(Badge).first()
        self.assertTrue(badge is queried_badge)
        self.assertEqual(queried_badge.title, 'testbadge')
        # references on the badged user
        self.assertEqual(badged_user.badges, [badge])
        self.assertEqual(badged_user.badges[0].users, [badged_user])

    def test_remove_badge_from_user(self):
        from adhocracy.model import meta, UserBadges
        creator, badged_user, badge = self._make_one()
        self.assertEqual(badged_user.badges, [badge])
        badged_user.badges.remove(badge)
        self.assertEqual(badged_user.badges, [])
        self.assertEqual(badge.users, [])
        self.assertEqual(meta.Session.query(UserBadges).count(), 0)

    def test_remove_user_from_badge(self):
        from adhocracy.model import meta, UserBadges
        creator, badged_user, badge = self._make_one()
        self.assertEqual(badge.users, [badged_user])
        badge.users.remove(badged_user)
        self.assertEqual(badge.users, [])
        self.assertEqual(badged_user.badges, [])
        self.assertEqual(meta.Session.query(UserBadges).count(), 0)

    def test_to_dict(self):
        creator, badged_user, badge = self._make_one()
        result = badge.to_dict()
        self.assert_(result['users'] == [u'badged_user'])


class TestDelegateableController(TestController):

    def _make_content(self):
        """Returns creator, delegateable and badge"""

        from adhocracy.model import DelegateableBadge, Proposal, Instance
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        delegateable = Proposal.create(instance, u"labeld", creator)
        badge = DelegateableBadge.create(u'testbadge', u'#ccc', 'description')

        return creator, delegateable, badge

    def test_delegateablebadges_created(self):
        #setup
        from adhocracy.model import DelegateableBadges, meta
        creator, delegateable, badge = self._make_content()
        # create the delegateable badge
        badge.assign(delegateable, creator)
        delegateablebadges = meta.Session.query(DelegateableBadges).first()
        self.assert_(delegateablebadges.creator is creator)
        self.assert_(delegateablebadges.delegateable is delegateable)
        self.assert_(delegateablebadges.badge is badge)
        # test the references on the badged delegateable
        self.assert_(delegateable.badges == [badge])
        # test the references on the badge
        self.assert_(delegateable.badges[0].delegateables \
                        == badge.delegateables \
                        == [delegateable])

    def test_remove_badge_from_delegateable(self):
        #setup
        from adhocracy.model import DelegateableBadges, meta
        creator, delegateable, badge = self._make_content()
        badge.assign(delegateable, creator)
        #remove badge from delegateable
        delegateable.badges.remove(badge)
        self.assert_(delegateable.badges == [])
        self.assert_(badge.delegateables == [])
        self.assert_(meta.Session.query(DelegateableBadges).count() == 0)

    def test_remove_delegateable_from_badge(self):
        #setup
        from adhocracy.model import DelegateableBadges, meta
        creator, delegateable, badge = self._make_content()
        badge.assign(delegateable, creator)
        #remove delegateable from badge
        badge.delegateables.remove(delegateable)
        self.assert_(badge.delegateables == [])
        self.assert_(delegateable.badges == [])
        self.assert_(meta.Session.query(DelegateableBadges).count() == 0)
