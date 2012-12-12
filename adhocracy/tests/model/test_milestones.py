# coding=utf-8
from datetime import datetime

from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_instance, tt_make_user


def _make_one(title, text, creator=None, time=None):
    from adhocracy.model import Instance, Milestone
    if creator is None:
        creator = tt_make_user()
    instance = Instance.find('test')
    now = datetime.now()
    milestone = Milestone.create(instance, creator, title, text, now)
    return (milestone, creator)


class TestMilestoneController(TestController):

    def test_create_milestone(self):
        from adhocracy.model import Instance, Milestone
        now = datetime.now()
        creator = tt_make_user()
        instance = Instance.find('test')
        milestone = Milestone.create(instance, creator, u'Titleü', u'Textü',
                                     now)
        self.assertEqual(milestone.instance, instance)
        self.assertEqual(milestone.creator, creator)
        self.assertEqual(len(Milestone.all()), 1)

    def test_create_milestone_with_category(self):
        from adhocracy.model import CategoryBadge
        milestone, creator = _make_one(u'title', u'text')
        category = CategoryBadge.create(u'Category', u'#ccc', True,
                                        u'descripiton', milestone.instance)
        milestone.category = category
        self.assertEqual(milestone.category.id, category.id)
        self.assertEqual(category.milestones, [milestone])

    def test_create_milestone_with_category_that_changes_instance(self):
        from adhocracy.model import CategoryBadge, meta
        milestone, creator = _make_one(u'title', u'text')
        category = CategoryBadge.create(u'Category', u'#ccc', True,
                                        u'descripiton', milestone.instance)
        milestone.category = category
        self.assertEqual(milestone.category.id, category.id)
        self.assertEqual(category.milestones, [milestone])

        # after we set another instance for the category (and refreshed
        # the objects in the Session), the milestone no longer has a category.
        other_instance = tt_make_instance(u'other', u'Other Label')
        category.instance = other_instance
        meta.Session.flush()
        meta.Session.refresh(milestone)
        meta.Session.refresh(category)
        self.assertNotEqual(category.instance, milestone.instance)
        self.assertEqual(milestone.category, None)
        self.assertEqual(category.milestones, [])
