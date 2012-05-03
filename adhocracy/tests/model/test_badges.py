# coding=utf-8
from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestBadgeController(TestController):

    def test_add_badge(self):
        from adhocracy.model import Badge, Instance, meta
        #add badge
        badge = Badge.create(u'badge ü', u'#ccc', u'description ü')
        self.assert_(str(badge) == '<Badge(1,badge ?)>')
        badge = Badge.find(u'badge ü')
        self.assert_(badge.instance == None)
        meta.Session.delete(badge)
        #we can set a flag if this badge is not for users (default)
        #but for delegateables
        self.assert_(badge.badge_delegateable == False)
        badge.badge_delegateable = True
        self.assert_(badge.badge_delegateable == True)
        #or if the badge is a delegateable category
        instance = Instance.find('test')
        badge = Badge.create(u'badge ü', u'#ccc', u'description ü',
                badge_delegateable_category=True,  instance=instance,)
        self.assert_(str(badge) == '<Badge(1,badge ?)>')
        self.assert_(badge.badge_delegateable_category == True)
        self.assert_(badge.instance != None)
        #cleanup
        meta.Session.delete(badge)
        meta.Session.commit()

    def test_to_dict(self):
        from adhocracy.model import Badge, Instance, meta
        instance = Instance.find('test')
        badge = Badge.create(u'badge', u'#ccc', u'description',
                badge_delegateable_category=True, instance=instance)
        result = badge.to_dict()
        self.assertEqual(result, {'color': u'#ccc', 'title': u'badge',
                                  'id': 1, 'users': [],
                                  'display_group': False, 'group': None,
                                  'instance': instance,
                                  'badge_delegateable_category': True,
                                  'badge_delegateable': False})
        #cleanup
        meta.Session.delete(badge)
        meta.Session.commit()

    def test_get_all_badgets(self):
        #setup
        from adhocracy.model import Badge, Instance, meta
        instance = Instance.find(u'test')
        user = Badge.create(u'badge ü', u'#ccc', u'description ü')
        user_instance = Badge.create(u'ü', u'#ccc', u'ü', instance=instance)
        delegateable = Badge.create(u'badge ü', u'#ccc', u'description ü',
                               badge_delegateable=True)
        delegateable_instance = Badge.create(u'badge ü', u'#ccc',
                                             u'description ü',
                                             badge_delegateable=True,
                                             instance=instance)
        category = Badge.create(u'badge ü', u'#ccc', u"desc",
                               badge_delegateable_category=True)
        category_instance = Badge.create(u'badge ü', u'#ccc', u"desc",
                                         badge_delegateable_category=True,
                                         instance=instance,)
        #all delegateable badges
        self.assert_(len(Badge.all_delegateable()) == 1)
        self.assert_(len(Badge.all_delegateable(instance=instance)) == 1)
        #all delegateable category badges
        self.assert_(len(Badge.all_delegateable_categories()) == 1)
        self.assert_(len(
            Badge.all_delegateable_categories(instance=instance)) == 1)
        #all user badgets
        self.assert_(len(Badge.all_user()) == 1)
        self.assert_(len(Badge.all_user(instance=instance)) == 1)
        #all badgets
        self.assert_(len(Badge.all()) == 3)
        self.assert_(len(Badge.all(instance=instance)) == 3)
        #realy all badgets
        self.assert_(len(Badge.all_q().all()) == 6)
        #cleanup
        meta.Session.delete(user)
        meta.Session.delete(user_instance)
        meta.Session.delete(delegateable_instance)
        meta.Session.delete(delegateable)
        meta.Session.delete(category)
        meta.Session.delete(category_instance)
        meta.Session.commit()


class TestUserController(TestController):

    def _make_one(self):
        """Returns creator, badged user and badge"""

        from adhocracy.model import Badge, UserBadge
        creator = tt_make_user('creator')
        badged_user = tt_make_user('badged_user')
        badge = Badge.create(u'testbadge', u'#ccc', u'description')
        UserBadge.create(badged_user, badge, creator)

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
        meta.Session.delete(badge)
        meta.Session.commit()

    def test_remove_badge_from_user(self):
        from adhocracy.model import meta, UserBadge
        creator, badged_user, badge = self._make_one()
        self.assertEqual(badged_user.badges, [badge])
        badged_user.badges.remove(badge)
        self.assertEqual(badged_user.badges, [])
        self.assertEqual(badge.users, [])
        self.assertEqual(meta.Session.query(UserBadge).count(), 0)
        meta.Session.delete(badge)
        meta.Session.commit()

    def test_remove_user_from_badge(self):
        from adhocracy.model import meta, UserBadge
        creator, badged_user, badge = self._make_one()
        self.assertEqual(badge.users, [badged_user])
        badge.users.remove(badged_user)
        self.assertEqual(badge.users, [])
        self.assertEqual(badged_user.badges, [])
        self.assertEqual(meta.Session.query(UserBadge).count(), 0)
        meta.Session.delete(badge)
        meta.Session.commit()

    def test_to_dict(self):
        from adhocracy.model import meta
        creator, badged_user, badge = self._make_one()
        result = badge.to_dict()
        self.assert_(result['users'] == [u'badged_user'])
        meta.Session.delete(badge)
        meta.Session.commit()


class TestDelegateableController(TestController):

    def _make_content(self):
        """Returns creator, delegateable and badge"""

        from adhocracy.model import Badge, Proposal, Instance
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        delegateable = Proposal.create(instance, u"labeld", creator,
                                       u'proposal description')
        badge = Badge.create(u'testbadge', u'#ccc', 'description')

        return creator, delegateable, badge

    def test_delegateablebadges_created(self):
        #setup
        from adhocracy.model import DelegateableBadge, meta
        creator, delegateable, badge = self._make_content()
        # create the delegateable badge
        delegateablebadge = DelegateableBadge.create(delegateable, badge,
                                                     creator)
        self.assert_(delegateablebadge.creator is creator)
        self.assert_(delegateablebadge.delegateable is delegateable)
        self.assert_(delegateablebadge.badge is badge)
        # test the references on the badged delegateable
        self.assert_(delegateable.badges == [badge])
        # test the references on the badge
        self.assert_(delegateable.badges[0].delegateables \
                        == badge.delegateables \
                        == [delegateable])
        meta.Session.delete(badge)
        meta.Session.commit()

    def test_remove_badge_from_delegateable(self):
        #setup
        from adhocracy.model import DelegateableBadge, meta
        creator, delegateable, badge = self._make_content()
        DelegateableBadge.create(delegateable, badge, creator)
        #remove badge from delegateable
        delegateable.badges.remove(badge)
        self.assert_(delegateable.badges == [])
        self.assert_(badge.delegateables == [])
        self.assert_(meta.Session.query(DelegateableBadge).count() == 0)
        meta.Session.delete(badge)
        meta.Session.commit()

    def test_remove_delegateable_from_badge(self):
        #setup
        from adhocracy.model import DelegateableBadge, meta
        creator, delegateable, badge = self._make_content()
        DelegateableBadge.create(delegateable, badge, creator)
        #remove delegateable from badge
        badge.delegateables.remove(delegateable)
        self.assert_(badge.delegateables == [])
        self.assert_(delegateable.badges == [])
        self.assert_(meta.Session.query(DelegateableBadge).count() == 0)
        meta.Session.delete(badge)
        meta.Session.commit()
