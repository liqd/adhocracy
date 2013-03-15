from adhocracy.tests import TestController


class TestBadgeHelper(TestController):

    def test_get_parent_badges_no_hierarchy(self):
        from adhocracy.model import UserBadge
        from adhocracy.lib.helpers.badge_helper import get_parent_badges
        badge = UserBadge.create('testbadge', '#ccc', True, 'description')
        result = [b.title for b in get_parent_badges(badge)]
        shouldbe = []
        self.assertEqual(result, shouldbe)

    def test_get_parent_badges_with_hierarchy(self):
        from adhocracy.model import CategoryBadge
        from adhocracy.lib.helpers.badge_helper import get_parent_badges
        badge0 = CategoryBadge.create('testbadge0', '#ccc', True, 'descr')
        badge11 = CategoryBadge.create('testbadge11', '#ccc', True, 'descr')
        badge12 = CategoryBadge.create('testbadge12', '#ccc', True, 'descr')
        badge121 = CategoryBadge.create('testbadge121', '#ccc', True, 'descr')
        badge11.parent = badge0
        badge12.parent = badge0
        badge121.parent = badge12
        result = [b.title for b in get_parent_badges(badge121)]
        shouldbe = ['testbadge12', 'testbadge0']
        self.assertEqual(result, shouldbe)
