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
                          u'#ccc', True, u'description ü')

    def test_get_all_badgets(self):
        #setup
        from adhocracy.model import Badge, CategoryBadge, DelegateableBadge, \
            InstanceBadge
        from adhocracy.model import UserBadge, Instance
        instance = Instance.find(u'test')
        # create for each type a global scope and an instance scope badge
        InstanceBadge.create(u'badge ü', u'#ccc', True, u'description ü')
        InstanceBadge.create(u'badge ü', u'#ccc', True, u'description ü',
                             instance=instance)
        UserBadge.create(u'badge ü', u'#ccc', True, u'description ü')
        UserBadge.create(u'ü', u'#ccc', True, u'ü', instance=instance)
        DelegateableBadge.create(u'badge ü', u'#ccc', True, u'description ü')
        DelegateableBadge.create(u'badge ü', u'#ccc', True, u'description ü',
                                 instance=instance)
        CategoryBadge.create(u'badge ü', u'#ccc', True, u"desc")
        CategoryBadge.create(u'badge ü', u'#ccc', True, u"desc",
                             instance=instance)

        # all instance badges
        self.assertEqual(len(InstanceBadge.all()), 1)
        self.assertEqual(len(InstanceBadge.all(instance=instance)), 1)
        # all delegateable badges
        self.assertEqual(len(DelegateableBadge.all()), 1)
        self.assertEqual(len(DelegateableBadge.all(instance=instance)), 1)
        # all delegateable category badges
        self.assertEqual(len(CategoryBadge.all()), 1)
        self.assertEqual(len(CategoryBadge.all(instance=instance)), 1)
        # all user badgets
        self.assertEqual(len(UserBadge.all()), 1)
        self.assertEqual(len(UserBadge.all(instance=instance)), 1)
        # We can get all Badges by using `Badge`
        self.assertEqual(len(Badge.all()), 4)
        self.assertEqual(len(Badge.all(instance=instance)), 4)

        self.assertEqual(len(Badge.all_q().all()), 8)


class TestUserController(TestController):

    def _make_one(self):
        """Returns creator, badged user and badge"""

        from adhocracy import model
        creator = tt_make_user('creator')
        badged_user = tt_make_user('badged_user')
        badge = model.UserBadge.create(u'testbadge', u'#ccc', True,
                                       u'description')
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
        self.assertEqual(result['users'], [u'badged_user'])


class TestDelegateableController(TestController):

    def _make_content(self):
        """Returns creator, delegateable and badge"""

        from adhocracy.model import DelegateableBadge, Proposal, Instance
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        delegateable = Proposal.create(instance, u"labeld", creator)
        badge = DelegateableBadge.create(u'testbadge', u'#ccc', True,
                                         'description')

        return creator, delegateable, badge

    def test_delegateablebadges_created(self):
        #setup
        from adhocracy.model import DelegateableBadges, meta
        creator, delegateable, badge = self._make_content()
        # create the delegateable badge
        badge.assign(delegateable, creator)
        delegateablebadges = meta.Session.query(DelegateableBadges).first()
        self.assertTrue(delegateablebadges.creator is creator)
        self.assertTrue(delegateablebadges.delegateable is delegateable)
        self.assertTrue(delegateablebadges.badge is badge)
        # test the references on the badged delegateable
        self.assertEqual(delegateable.badges, [badge])
        # test the references on the badge
        self.assertTrue(delegateable.badges[0].delegateables
                        == badge.delegateables
                        == [delegateable])

    def test_remove_badge_from_delegateable(self):
        #setup
        from adhocracy.model import DelegateableBadges, meta
        creator, delegateable, badge = self._make_content()
        badge.assign(delegateable, creator)
        #remove badge from delegateable
        delegateable.badges.remove(badge)
        self.assertEqual(delegateable.badges, [])
        self.assertEqual(badge.delegateables, [])
        self.assertEqual(meta.Session.query(DelegateableBadges).count(), 0)

    def test_remove_delegateable_from_badge(self):
        #setup
        from adhocracy.model import DelegateableBadges, meta
        creator, delegateable, badge = self._make_content()
        badge.assign(delegateable, creator)
        #remove delegateable from badge
        badge.delegateables.remove(delegateable)
        self.assertEqual(badge.delegateables, [])
        self.assertEqual(delegateable.badges, [])
        self.assertEqual(meta.Session.query(DelegateableBadges).count(), 0)


class TestCategoryController(TestController):

    def _make_content(self):
        """Returns creator, delegateable and badge"""

        from adhocracy.model import CategoryBadge, Proposal, Instance
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        delegateable = Proposal.create(instance, u"labeld", creator)
        badge = CategoryBadge.create(u'testbadge', u'#ccc', True,
                                     'description')

        return creator, delegateable, badge

    def test_categorybadges_created(self):
        #setup
        from adhocracy.model import DelegateableBadges, meta
        creator, delegateable, badge = self._make_content()
        # create the delegateable badge
        badge.assign(delegateable, creator)
        delegateablebadges = meta.Session.query(DelegateableBadges).first()
        self.assertTrue(delegateablebadges.creator is creator)
        self.assertTrue(delegateablebadges.delegateable is delegateable)
        self.assertTrue(delegateablebadges.badge is badge)

    def test_categorybadges_hierarchy(self):
        #setup
        from adhocracy.model import CategoryBadge
        creator, delegateable, badge = self._make_content()
        badge_parent = CategoryBadge.create(u'badge parent', u'#ccc', True,
                                            'description')
        badge_parent.select_child_description = "choose child"
        # create the delegateable badge
        badge.assign(delegateable, creator)
        # add parent badge
        badge.parent = badge_parent
        self.assertEqual(badge.parent, badge_parent)
        self.assertTrue(badge in badge_parent.children)
        self.assertEqual(badge_parent.select_child_description, "choose child")
        self.assertTrue(badge_parent.parent is None)

    def test_to_dict_category(self):
        #setup
        creator, delegateable, badge = self._make_content()
        # create the delegateable badge
        badge.assign(delegateable, creator)
        # test dict
        result = badge.to_dict()
        result = sorted(result.items())
        expected = {'color': u'#ccc',
                    'description': u'description',
                    'id': 1,
                    'instance': None,
                    'title': u'testbadge',
                    'visible': True,
                    'parent': None,
                    'select_child_description': u'',
                    }
        expected = sorted(expected.items())
        self.assertEqual(result, expected)


class TestInstanceController(TestController):

    def _make_content(self):
        """Returns creator, delegateable and badge"""

        from adhocracy.model import InstanceBadge, Instance
        creator = tt_make_user('creator')
        instance = Instance.create("instance2", u"instance2", creator)
        badge = InstanceBadge.create(u'testbadge', u'#ccc2', True,
                                     'description')

        return creator, instance, badge

    def test_instancebadges_created(self):
        #setup
        from adhocracy.model import InstanceBadges, meta
        creator, instance, badge = self._make_content()
        # create the instance badge
        badge.assign(instance, creator)
        instancebadges = meta.Session.query(InstanceBadges).first()
        self.assertTrue(instancebadges.creator is creator)
        self.assertTrue(instancebadges.instance is instance)
        self.assertTrue(instancebadges.badge is badge)
        # test the references on the badged instance
        self.assertEqual(instance.badges, [badge])
        # test the references on the badge
        self.assertTrue(instance.badges[0].instances
                        == badge.instances
                        == [instance])

    def test_remove_badge_from_instance(self):
        #setup
        from adhocracy.model import InstanceBadges, meta
        creator, instance, badge = self._make_content()
        badge.assign(instance, creator)
        #remove badge from instance
        instance.badges.remove(badge)
        self.assertEqual(instance.badges, [])
        self.assertEqual(badge.instances, [])
        self.assertEqual(meta.Session.query(InstanceBadges).count(), 0)

    def test_remove_instance_from_badge(self):
        #setup
        from adhocracy.model import InstanceBadges, meta
        creator, instance, badge = self._make_content()
        badge.assign(instance, creator)
        #remove instance from badge
        badge.instances.remove(instance)
        self.assertEqual(badge.instances, [])
        self.assertEqual(instance.badges, [])
        self.assertEqual(meta.Session.query(InstanceBadges).count(), 0)
