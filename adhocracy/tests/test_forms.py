from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestValidators(TestController):

    def test_valid_badge(self):
        from adhocracy.forms import ValidBadge
        from adhocracy.model import Badge, UserBadge

        creator = tt_make_user('creator')
        badged_user = tt_make_user('badged_user')
        badge = Badge.create('testbadge', '#ccc', 'description')
        UserBadge.create(badged_user, badge, creator)
        value = ValidBadge.to_python(badge.id, None)
        self.assertEqual(value, badge)

    def test_invalid_badge(self):
        from formencode import Invalid
        from adhocracy.forms import ValidBadge
        from adhocracy.model import Badge, UserBadge

        creator = tt_make_user('creator')
        badged_user = tt_make_user('badged_user')
        badge = Badge.create('testbadge', '#ccc', 'description')
        UserBadge.create(badged_user, badge, creator)
        self.assertRaises(Invalid, ValidBadge.to_python,
                          badge.id + 1, state=None)

    def test_username_contains_char(self):
        from adhocracy.forms import ContainsChar
        validator = ContainsChar()
        value = validator.to_python('ba12', None)
        self.assertEqual(value, 'ba12')

    def test_username_contains_no_char(self):
        from formencode import Invalid
        from adhocracy.forms import ContainsChar
        self.assertRaises(Invalid, ContainsChar.to_python, '1234', None)
