# coding=utf-8
from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestBadgeController(TestController): 
  
    def test_add_badge(self):
        from adhocracy.model import Badge
        #add badge
        badge = Badge.create(u'badge ü', u'#ccc', u'description ü') 
        self.assert_(str(badge) == '<Badge(1,badge ?)>')
        #We can set a flag if this badge should be uses with users (default)
        #or with delegateables
        self.assert_(badge.badge_delegateable == False)
        badge.badge_delegateable = True
        self.assert_(badge.badge_delegateable == True)

    def test_to_dict(self):
        from adhocracy.model import Badge
        badge = Badge.create(u'badge', u'#ccc', u'description') 
        result = badge.to_dict()
        self.assertEqual(result, {'color': u'#ccc', 'title': u'badge',
                                  'id': 1, 'users': [],
                                  'display_group': False, 'group': None,
                                  'badge_delegateable': False})


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
        self.assertEqual(meta.Session.query(Badge).count(), 1)
        queried_badge = meta.Session.query(Badge).first()
        self.assertTrue(badge is queried_badge)
        self.assertEqual(queried_badge.title, 'testbadge')
        # references on the badged user
        self.assertEqual(badged_user.badges, [badge])
        self.assertEqual(badged_user.badges[0].users, [badged_user])

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
        self.assert_(result['users'] == [u'badged_user'])


class TestDelegateableController(TestController):
    
    def _make_content(self):
        """Returns creator, delegateable and badge"""

        from adhocracy.model import Badge, Proposal, Instance
        instance = Instance.find('test')
        creator = tt_make_user('creator')
        delegateable = Proposal.create(instance, u"labeld", creator)
        badge = Badge.create(u'testbadge', u'#ccc', 'description')

        return creator, delegateable, badge
  
    def test_delegateablebadges_created(self):
        #setup
        from adhocracy.model import DelegateableBadge
        creator, delegateable, badge = self._make_content()
        # create the delegateable badge
        delegateablebadge = DelegateableBadge.create(delegateable, badge, creator)
        self.assert_(delegateablebadge.creator is creator)
        self.assert_(delegateablebadge.delegateable is delegateable)
        self.assert_(delegateablebadge.badge is badge)
        # test the references on the badged delegateable
        self.assert_(delegateable.badges == [badge])
        # test the references on the badge
        self.assert_(delegateable.badges[0].delegateables \
                        == badge.delegateables \
                        == [delegateable])

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
