from adhocracy.tests import TestController
from adhocracy.tests.testtools import tt_get_instance, tt_make_instance


class TestValidators(TestController):

    def test_valid_user_badge(self):
        from adhocracy.forms import ValidUserBadge
        from adhocracy.model import UserBadge

        badge = UserBadge.create('testbadge', '#ccc', True, 'description')
        value = ValidUserBadge.to_python(badge.id, None)
        self.assertEqual(value, badge)

    def test_invalid_user_badge(self):
        from formencode import Invalid
        from adhocracy.forms import ValidUserBadge
        from adhocracy.model import UserBadge

        badge = UserBadge.create('testbadge', '#ccc', True, 'description')
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

    def test_valid_category_badge(self):
        from formencode import Invalid
        from adhocracy.forms import ValidCategoryBadge
        from adhocracy.model import CategoryBadge, instance_filter

        # the currently set instance ist the test instance. CategoryBadges from
        # the current instance are valid.
        test_instance = tt_get_instance()
        self.assertEqual(test_instance, instance_filter.get_instance())
        test_category = CategoryBadge.create('test_category', '#ccc', True,
                                             'description', test_instance)
        value = ValidCategoryBadge.to_python(str(test_category.id))
        self.assertEqual(value, test_category)

        # from other instances they are not valid
        other_instance = tt_make_instance('other', 'Other Instance')
        other_category = CategoryBadge.create('other_category', '#ccc', True,
                                              'description', other_instance)
        self.assertRaises(Invalid, ValidCategoryBadge.to_python,
                          str(other_category.id))

    def test_valid_category_badge_if_empty(self):
        from adhocracy.forms import ValidCategoryBadge
        validator = ValidCategoryBadge(if_empty=None)
        value = validator.to_python('')
        self.assertEqual(value, None)

    def test_valid_imagefile_upload(self):
        from adhocracy.forms.common import ValidImageFileUpload
        from formencode import Invalid
        from cgi import FieldStorage
        from io import BytesIO
        value = FieldStorage()
        value.file = BytesIO(b"binarydata")
        value.filename = "test.png"
        value.name = "thumbs"
        self.assertRaises(Invalid, ValidImageFileUpload.to_python, value)

    def test_valid_file_upload(self):
        from adhocracy.forms.common import ValidFileUpload
        from formencode import Invalid
        from cgi import FieldStorage
        from io import BytesIO
        ValidFileUpload.max_size = 1
        value = FieldStorage()
        value.file = BytesIO(b"bi")
        value.filename = "test.png"
        value.name = "thumbs"
        self.assertRaises(Invalid, ValidFileUpload.to_python, value)
