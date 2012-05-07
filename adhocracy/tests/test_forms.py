from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_make_user


class TestValidators(TestController):

    def test_valid_user_badge(self):
        from adhocracy.forms import ValidUserBadge
        from adhocracy.model import UserBadge

        badge = UserBadge.create('testbadge', '#ccc', 'description')
        value = ValidUserBadge.to_python(badge.id, None)
        self.assertEqual(value, badge)

    def test_invalid_user_badge(self):
        from formencode import Invalid
        from adhocracy.forms import ValidUserBadge
        from adhocracy.model import UserBadge

        badge = UserBadge.create('testbadge', '#ccc', 'description')
        self.assertRaises(Invalid, ValidUserBadge.to_python,
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
